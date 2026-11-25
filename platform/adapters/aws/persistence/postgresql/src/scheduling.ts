import { outboxEntryId } from "@kanbien/core/persistence";
import { entityId, err, isoDateTimeFromDate, uuid } from "@kanbien/core/shared";
import { platformJobName } from "@kanbien/platform-contracts";
import {
  capturePlatformPersistenceDiagnostic,
  observePlatformPersistenceDiagnostic,
  persistenceScheduleRejectionDiagnosticRecord,
  persistenceScheduleStoreRejectionDiagnosticRecord,
  persistenceScheduleStoredRecordDiagnosticRecord,
  platformPersistenceError,
  platformOutboxRecord,
  type PlatformPersistenceDiagnosticOptions,
  type PlatformSchedule,
  type PlatformScheduleHandover,
  type PlatformScheduleStore,
} from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool } from "./connection";
import type { PostgreSqlPersistenceConfiguration } from "./configuration/index";
import { isPostgreSqlUniqueViolation, postgreSqlPersistenceOperationError } from "./errors";
import { outboxInsertStatement, relation } from "./records";
import { withPostgreSqlTransaction } from "./transactions";

export interface PostgreSqlPlatformScheduleStoreOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: PostgreSqlPersistenceConfiguration;
  readonly pool: PostgreSqlConnectionPool;
}

interface PostgreSqlScheduleRow {
  readonly id: string;
  readonly job_name: string;
  readonly due_at: Date;
  readonly state: string;
  readonly outbox_entry_id: string | null;
}

/** Stores an already validated, one-off schedule record in the selected schema. */
export function createPostgreSqlPlatformScheduleStore(
  options: PostgreSqlPlatformScheduleStoreOptions,
): PlatformScheduleStore {
  const table = relation(options.configuration.schema, "platform_schedule", options);
  return {
    create: async (schedule) => {
      try {
        const created = await options.pool.query<PostgreSqlScheduleRow>({
          text: `INSERT INTO ${table} (id, job_name, due_at, state) VALUES ($1, $2, $3, $4) RETURNING id, job_name, due_at, state, outbox_entry_id`,
          values: [String(schedule.id), String(schedule.jobName), schedule.dueAt, schedule.state],
        });
        const decoded = created.rows[0] === undefined
          ? scheduleStoredFailure(options, "create", "returned", "unknown", "row", "absent")
          : scheduleFromRow(created.rows[0], options, "create", "returned", "unknown");
        return decoded;
      } catch (cause) {
        if (isPostgreSqlUniqueViolation(cause)) return duplicateSchedule(options);
        return { ok: false, error: postgreSqlPersistenceOperationError("create_schedule", cause, options) };
      }
    },
    get: async (id) => {
      try {
        const read = await options.pool.query<PostgreSqlScheduleRow>({
          text: `SELECT id, job_name, due_at, state, outbox_entry_id FROM ${table} WHERE id = $1`,
          values: [String(id)],
        });
        if (read.rows[0] === undefined) return null;
        const decoded = scheduleFromRow(read.rows[0], options, "read", "returned", "not-assessed");
        if (decoded.ok) return decoded.value;
        throw decoded.error;
      } catch (cause) {
        if (isPlatformScheduleStoredStateError(cause)) throw cause;
        throw postgreSqlPersistenceOperationError("read_schedule", cause, options);
      }
    },
    listDue: async ({ asOf, limit }) => {
      if (!Number.isInteger(limit) || limit <= 0 || limit > 100) return err(platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LIMIT",
        defaultMessage: "Schedule delivery limit must be an integer between 1 and 100.",
        messageKey: "platform.persistence.schedule.limit.invalid",
        diagnosticRecord: persistenceScheduleRejectionDiagnosticRecord({ operation: "list-due", field: "limit", condition: !Number.isInteger(limit) ? "not-integer" : limit <= 0 ? "not-positive" : "too-large", effect: "local-state-unchanged" }),
      }));
      try {
        const read = await options.pool.query<PostgreSqlScheduleRow>({
          text: `SELECT id, job_name, due_at, state, outbox_entry_id FROM ${table} WHERE state = 'waiting' AND due_at <= $1 ORDER BY due_at ASC, id ASC LIMIT $2`,
          values: [asOf, limit],
        });
        const schedules = read.rows.map(row => scheduleFromRow(row, options, "list-due", "returned", "not-assessed"));
        const failure = schedules.find(result => !result.ok);
        if (failure !== undefined && !failure.ok) return failure;
        return { ok: true as const, value: schedules.map(result => (result as { readonly ok: true; readonly value: PlatformSchedule }).value) };
      } catch (cause) {
        return { ok: false as const, error: postgreSqlPersistenceOperationError("list_due_schedules", cause, options) };
      }
    },
    handoverDue: async ({ scheduleId, asOf, outboxEntry }) => {
      const handedOver = await withPostgreSqlTransaction<PlatformScheduleHandover, import("@kanbien/platform-persistence").PlatformPersistenceError>(options, async client => {
        try {
          const selected = await client.query<PostgreSqlScheduleRow>({
            text: `SELECT id, job_name, due_at, state, outbox_entry_id FROM ${table} WHERE id = $1 FOR UPDATE`, values: [String(scheduleId)],
          });
          if (selected.rows[0] === undefined) return err(scheduleNotFound(options));
          const decoded = scheduleFromRow(selected.rows[0], options, "handover", "returned", "unknown");
          if (!decoded.ok) return decoded;
          if (decoded.value.state === "delivery-created") return { ok: true as const, value: { disposition: "outbox-already-created", schedule: decoded.value } };
          if (Date.parse(decoded.value.dueAt) > Date.parse(asOf)) return { ok: true as const, value: { disposition: "not-due", schedule: decoded.value } };
          await client.query(outboxInsertStatement(options.configuration.schema, outboxEntry));
          const updated = await client.query<PostgreSqlScheduleRow>({
            text: `UPDATE ${table} SET state = 'delivery-created', outbox_entry_id = $2 WHERE id = $1 RETURNING id, job_name, due_at, state, outbox_entry_id`,
            values: [String(scheduleId), String(outboxEntry.id)],
          });
          if (updated.rows[0] === undefined) return scheduleStoredFailure(options, "handover", "returned", "unknown", "row", "absent");
          const handedOffSchedule = scheduleFromRow(updated.rows[0], options, "handover", "returned", "unknown");
          if (!handedOffSchedule.ok) return handedOffSchedule;
          return { ok: true as const, value: { disposition: "outbox-created", schedule: handedOffSchedule.value,
            outbox: platformOutboxRecord({ entry: outboxEntry }) } };
        } catch (cause) {
          return err(postgreSqlPersistenceOperationError("handover_schedule", cause, options));
        }
      });
      return handedOver;
    },
  };
}

function scheduleFromRow(
  row: PostgreSqlScheduleRow,
  options: PostgreSqlPlatformScheduleStoreOptions,
  operation: "create" | "read" | "list-due" | "handover",
  reduction: "returned" | "null",
  effect: "unknown" | "not-assessed",
) {
  const id = uuid(row.id);
  if (!id.ok) return scheduleStoredFailure(options, operation, reduction, effect, "id", "invalid");
  const jobName = platformJobName(row.job_name);
  if (!jobName.ok) return scheduleStoredFailure(options, operation, reduction, effect, "job-name", "invalid");
  if (!(row.due_at instanceof Date) || Number.isNaN(row.due_at.getTime())) return scheduleStoredFailure(options, operation, reduction, effect, "due-at", "invalid");
  if (row.state !== "waiting" && row.state !== "delivery-created") return scheduleStoredFailure(options, operation, reduction, effect, "state", "invalid");
  if (row.state === "waiting" && row.outbox_entry_id !== null) return scheduleStoredFailure(options, operation, reduction, effect, "outbox-entry", "invalid");
  if (row.state === "delivery-created" && (typeof row.outbox_entry_id !== "string" || row.outbox_entry_id.length === 0)) return scheduleStoredFailure(options, operation, reduction, effect, "outbox-entry", "invalid");
  try {
    return { ok: true as const, value: {
      id: entityId<"PlatformScheduleId">(id.value),
      jobName: jobName.value,
      dueAt: isoDateTimeFromDate(row.due_at),
      state: row.state,
      ...(row.outbox_entry_id === null ? {} : { outboxEntryId: outboxEntryId(row.outbox_entry_id) }),
    } satisfies PlatformSchedule };
  } catch (cause) {
    return scheduleStoredFailure(options, operation, reduction, effect, "due-at", "invalid", cause);
  }
}

function scheduleStoredFailure(
  options: PostgreSqlPlatformScheduleStoreOptions,
  operation: "create" | "read" | "list-due" | "handover",
  reduction: "returned" | "null",
  effect: "unknown" | "not-assessed",
  field: "row" | "id" | "job-name" | "due-at" | "state" | "outbox-entry",
  condition: "absent" | "invalid",
  cause?: unknown,
) {
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => persistenceScheduleStoredRecordDiagnosticRecord({ operation, reduction, effect, field, condition }));
  observePlatformPersistenceDiagnostic(options, diagnosticRecord, cause);
  return { ok: false as const, error: platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "Stored schedule state is invalid.",
    messageKey: "platform.persistence.schedule.stored.invalid",
    diagnosticRecord,
    ...(cause === undefined ? {} : { cause }),
  }) };
}

function duplicateSchedule(options: PostgreSqlPlatformScheduleStoreOptions) {
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => persistenceScheduleStoreRejectionDiagnosticRecord({ operation: "create", field: "id", condition: "duplicate", effect: "unknown" }));
  observePlatformPersistenceDiagnostic(options, diagnosticRecord);
  return { ok: false as const, error: platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_DUPLICATE_SCHEDULE",
    defaultMessage: "Schedule already exists.",
    messageKey: "platform.persistence.schedule.duplicate",
    diagnosticRecord,
  }) };
}

function scheduleNotFound(options: PostgreSqlPlatformScheduleStoreOptions) {
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => persistenceScheduleRejectionDiagnosticRecord({ operation: "handover", field: "schedule", condition: "not-found", effect: "local-state-unchanged" }));
  observePlatformPersistenceDiagnostic(options, diagnosticRecord);
  return platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_SCHEDULE_NOT_FOUND",
    defaultMessage: "Schedule was not found.",
    messageKey: "platform.persistence.schedule.not_found",
    diagnosticRecord,
  });
}

function isPlatformScheduleStoredStateError(cause: unknown): cause is ReturnType<typeof platformPersistenceError> {
  return typeof cause === "object" && cause !== null && (cause as { code?: unknown }).code === "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED"
    && (cause as { messageKey?: unknown }).messageKey === "platform.persistence.schedule.stored.invalid";
}
