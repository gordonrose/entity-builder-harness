import { outboxEntryId, recordId, recordKind, recordReference, type RecordReference } from "@kanbien/core/persistence";
import { entityId, err, isoDateTimeFromDate, uuid, type ISODateTime } from "@kanbien/core/shared";
import { platformJobName } from "@kanbien/platform-contracts";
import {
  capturePlatformPersistenceDiagnostic,
  observePlatformPersistenceDiagnostic,
  persistenceScheduleRejectionDiagnosticRecord,
  persistenceScheduleStoreRejectionDiagnosticRecord,
  persistenceScheduleStoredRecordDiagnosticRecord,
  persistenceScheduleSubjectDiagnosticRecord,
  persistenceScheduleControlStoredRecordDiagnosticRecord,
  persistenceScheduleControlRejectionDiagnosticRecord,
  persistenceScheduleInvalidRowBlockedDiagnosticRecord,
  platformPersistenceError,
  platformOutboxRecord,
  type PlatformPersistenceDiagnosticOptions,
  type PlatformPersistenceError,
  type PlatformSchedule,
  type PlatformScheduleHandover,
  type PlatformScheduleStore,
  type PersistenceScheduleSubjectDetail,
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
  readonly subject_kind: string | null;
  readonly subject_id: string | null;
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
          text: `INSERT INTO ${table} (id, job_name, due_at, state, subject_kind, subject_id) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id`,
          values: [String(schedule.id), String(schedule.jobName), schedule.dueAt, schedule.state, schedule.subject?.kind ?? null, schedule.subject?.id ?? null],
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
          text: `SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM ${table} WHERE id = $1`,
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
    listDue: async ({ asOf, limit, blockInvalid }) => {
      if (!Number.isInteger(limit) || limit <= 0 || limit > 100) return err(platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_LIMIT",
        defaultMessage: "Schedule delivery limit must be an integer between 1 and 100.",
        messageKey: "platform.persistence.schedule.limit.invalid",
        diagnosticRecord: persistenceScheduleRejectionDiagnosticRecord({ operation: "list-due", field: "limit", condition: !Number.isInteger(limit) ? "not-integer" : limit <= 0 ? "not-positive" : "too-large", effect: "local-state-unchanged" }),
      }));
      if (blockInvalid === true) return selectDueAndBlockInvalid(options, table, asOf, limit);
      try {
        const read = await options.pool.query<PostgreSqlScheduleRow>({
          text: `SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM ${table} WHERE state = 'waiting' AND due_at <= $1 ORDER BY due_at ASC, id ASC LIMIT $2`,
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
    blockDue: ({ scheduleId, asOf }) => controlSchedule(options, table, "block", String(scheduleId), asOf),
    resumeBlocked: scheduleId => controlSchedule(options, table, "resume", String(scheduleId)),
    handoverDue: async ({ scheduleId, asOf, outboxEntry }) => {
      const handedOver = await withPostgreSqlTransaction<PlatformScheduleHandover, import("@kanbien/platform-persistence").PlatformPersistenceError>(options, async client => {
        try {
          const selected = await client.query<PostgreSqlScheduleRow>({
            text: `SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM ${table} WHERE id = $1 FOR UPDATE`, values: [String(scheduleId)],
          });
          if (selected.rows[0] === undefined) return err(scheduleNotFound(options));
          const decoded = scheduleFromRow(selected.rows[0], options, "handover", "returned", "unknown");
          if (!decoded.ok) return decoded;
          if (decoded.value.state === "delivery-created") return { ok: true as const, value: { disposition: "outbox-already-created", schedule: decoded.value } };
          if (decoded.value.state === "blocked-job-unavailable" || decoded.value.state === "blocked-invalid-row") return { ok: true as const, value: { disposition: "blocked", schedule: decoded.value } };
          if (Date.parse(decoded.value.dueAt) > Date.parse(asOf)) return { ok: true as const, value: { disposition: "not-due", schedule: decoded.value } };
          await client.query(outboxInsertStatement(options.configuration.schema, outboxEntry));
          const updated = await client.query<PostgreSqlScheduleRow>({
            text: `UPDATE ${table} SET state = 'delivery-created', outbox_entry_id = $2 WHERE id = $1 RETURNING id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id`,
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
  operation: "create" | "read" | "list-due" | "handover" | "block" | "resume",
  reduction: "returned" | "null",
  effect: "unknown" | "not-assessed",
) {
  const id = uuid(row.id);
  if (!id.ok) return scheduleStoredFailure(options, operation, reduction, effect, "id", "invalid");
  const jobName = platformJobName(row.job_name);
  if (!jobName.ok) return scheduleStoredFailure(options, operation, reduction, effect, "job-name", "invalid");
  if (!(row.due_at instanceof Date) || Number.isNaN(row.due_at.getTime())) return scheduleStoredFailure(options, operation, reduction, effect, "due-at", "invalid");
  if (row.state !== "waiting" && row.state !== "delivery-created" && row.state !== "blocked-job-unavailable" && row.state !== "blocked-invalid-row") return scheduleStoredFailure(options, operation, reduction, effect, "state", "invalid");
  if (row.state !== "delivery-created" && row.outbox_entry_id !== null) return scheduleStoredFailure(options, operation, reduction, effect, "outbox-entry", "invalid");
  if (row.state === "delivery-created" && (typeof row.outbox_entry_id !== "string" || row.outbox_entry_id.length === 0)) return scheduleStoredFailure(options, operation, reduction, effect, "outbox-entry", "invalid");
  let subject: RecordReference | undefined;
  if (row.subject_kind !== null || row.subject_id !== null) {
    if (row.subject_kind === null || row.subject_id === null) return scheduleSubjectFailure(options, { operation, effect, field: "subject-pair", condition: "partial" });
    if (typeof row.subject_kind !== "string") return scheduleSubjectFailure(options, { operation, effect, field: "subject-kind", condition: "invalid" });
    if (typeof row.subject_id !== "string") return scheduleSubjectFailure(options, { operation, effect, field: "subject-id", condition: "invalid" });
    const kind = recordKind(row.subject_kind);
    const id = recordId(row.subject_id);
    if (!kind.ok) return scheduleSubjectFailure(options, { operation, effect, field: "subject-kind", condition: "invalid" });
    if (!id.ok) return scheduleSubjectFailure(options, { operation, effect, field: "subject-id", condition: "invalid" });
    subject = recordReference({ kind: kind.value, id: id.value });
  }
  try {
    return { ok: true as const, value: {
      id: entityId<"PlatformScheduleId">(id.value),
      jobName: jobName.value,
      dueAt: isoDateTimeFromDate(row.due_at),
      state: row.state,
      ...(subject === undefined ? {} : { subject }),
      ...(row.outbox_entry_id === null ? {} : { outboxEntryId: outboxEntryId(row.outbox_entry_id) }),
    } satisfies PlatformSchedule };
  } catch (cause) {
    return scheduleStoredFailure(options, operation, reduction, effect, "due-at", "invalid", cause);
  }
}

function scheduleSubjectFailure(options: PostgreSqlPlatformScheduleStoreOptions, detail: PersistenceScheduleSubjectDetail) {
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => persistenceScheduleSubjectDiagnosticRecord(detail));
  observePlatformPersistenceDiagnostic(options, diagnosticRecord);
  return err(platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "Stored schedule state is invalid.",
    messageKey: "platform.persistence.schedule.stored.invalid",
    diagnosticRecord,
  }));
}

function scheduleStoredFailure(
  options: PostgreSqlPlatformScheduleStoreOptions,
  operation: "create" | "read" | "list-due" | "handover" | "block" | "resume",
  reduction: "returned" | "null",
  effect: "unknown" | "not-assessed",
  field: "row" | "id" | "job-name" | "due-at" | "state" | "outbox-entry",
  condition: "absent" | "invalid",
  cause?: unknown,
) {
  const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => operation === "block" || operation === "resume"
    ? persistenceScheduleControlStoredRecordDiagnosticRecord({ operation, reduction, effect, field, condition })
    : persistenceScheduleStoredRecordDiagnosticRecord({ operation, reduction, effect, field, condition }));
  observePlatformPersistenceDiagnostic(options, diagnosticRecord, cause);
  return { ok: false as const, error: platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED",
    defaultMessage: "Stored schedule state is invalid.",
    messageKey: "platform.persistence.schedule.stored.invalid",
    diagnosticRecord,
    ...(cause === undefined ? {} : { cause }),
  }) };
}

async function controlSchedule(options: PostgreSqlPlatformScheduleStoreOptions, table: string,
  operation: "block" | "resume", scheduleId: string, asOf?: string) {
  if (operation === "resume") return resumeRepairedSchedule(options, table, scheduleId);
  const columns = "id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id";
  try {
    const updated = await options.pool.query<PostgreSqlScheduleRow>({
      text: `UPDATE ${table} SET state = 'blocked-job-unavailable' WHERE id = $1 AND state = 'waiting' AND due_at <= $2 RETURNING ${columns}`,
      values: [scheduleId, asOf],
    });
    const row = updated.rows[0] ?? (await options.pool.query<PostgreSqlScheduleRow>({
      text: `SELECT ${columns} FROM ${table} WHERE id = $1`, values: [scheduleId],
    })).rows[0];
    if (row === undefined) {
      const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => persistenceScheduleControlRejectionDiagnosticRecord(operation));
      observePlatformPersistenceDiagnostic(options, diagnosticRecord);
      return err(platformPersistenceError({ code: "PLATFORM_PERSISTENCE_SCHEDULE_NOT_FOUND", defaultMessage: "Schedule was not found.", diagnosticRecord }));
    }
    return scheduleFromRow(row, options, operation, "returned", "unknown");
  } catch (cause) {
    return err(postgreSqlPersistenceOperationError("block_schedule", cause, options));
  }
}

/** Lock only this bounded page; invalid records are retained, never fabricated or delivered. */
async function selectDueAndBlockInvalid(options: PostgreSqlPlatformScheduleStoreOptions, table: string, asOf: ISODateTime, limit: number) {
  let blocked = 0;
  const selected = await withPostgreSqlTransaction<readonly PlatformSchedule[], import("@kanbien/platform-persistence").PlatformPersistenceError>(options, async client => {
    try {
      const rows = await client.query<PostgreSqlScheduleRow>({
        text: `SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM ${table} WHERE state = 'waiting' AND due_at <= $1 ORDER BY due_at ASC, id ASC LIMIT $2 FOR UPDATE SKIP LOCKED`,
        values: [asOf, limit],
      });
      const valid: PlatformSchedule[] = [];
      const invalid: { readonly id: string; readonly error: PlatformPersistenceError }[] = [];
      for (const row of rows.rows) {
        const decoded = scheduleFromRow(row, options, "list-due", "returned", "not-assessed");
        if (decoded.ok) { valid.push(decoded.value); continue; }
        // PostgreSQL's uuid column provides an address; fake/broken provider output must still fail closed.
        if (!uuid(row.id).ok) return decoded;
        invalid.push({ id: row.id, error: decoded.error });
      }
      const firstInvalid = invalid[0];
      if (firstInvalid !== undefined) {
        // One round trip for the bounded page, not one per corrupt row: the caller's time budget
        // must cover this entire atomic operation before another continuation check is possible.
        const ids = invalid.map(row => row.id);
        const isolated = await client.query<{ readonly id: string }>({
          text: `UPDATE ${table} SET state = 'blocked-invalid-row' WHERE id = ANY($1::uuid[]) AND state = 'waiting' RETURNING id`, values: [ids],
        });
        const returnedIds = new Set(isolated.rows.map(row => row.id));
        if (isolated.rowCount !== ids.length || isolated.rows.length !== ids.length || returnedIds.size !== ids.length
          || ids.some(id => !returnedIds.has(id))) return err(firstInvalid.error);
        blocked = ids.length;
      }
      return { ok: true, value: valid };
    } catch (cause) { return err(postgreSqlPersistenceOperationError("list_due_schedules", cause, options)); }
  });
  if (selected.ok) for (let index = 0; index < blocked; index++) {
    observePlatformPersistenceDiagnostic(options, capturePlatformPersistenceDiagnostic(() => persistenceScheduleInvalidRowBlockedDiagnosticRecord()));
  }
  return selected;
}

/** A failed repair never releases an invalid record back into the due scan. */
async function resumeRepairedSchedule(options: PostgreSqlPlatformScheduleStoreOptions, table: string, scheduleId: string) {
  return withPostgreSqlTransaction<PlatformSchedule, import("@kanbien/platform-persistence").PlatformPersistenceError>(options, async client => {
    try {
      const read = await client.query<PostgreSqlScheduleRow>({
        text: `SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM ${table} WHERE id = $1 FOR UPDATE`, values: [scheduleId],
      });
      if (read.rows[0] === undefined) return err(platformPersistenceError({ code: "PLATFORM_PERSISTENCE_SCHEDULE_NOT_FOUND",
        defaultMessage: "Schedule was not found.", diagnosticRecord: capturePlatformPersistenceDiagnostic(() => persistenceScheduleControlRejectionDiagnosticRecord("resume")) }));
      const current = scheduleFromRow(read.rows[0], options, "resume", "returned", "not-assessed");
      if (!current.ok) return current;
      if (current.value.state !== "blocked-job-unavailable" && current.value.state !== "blocked-invalid-row") return current;
      const updated = await client.query<PostgreSqlScheduleRow>({
        text: `UPDATE ${table} SET state = 'waiting' WHERE id = $1 RETURNING id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id`, values: [scheduleId],
      });
      return updated.rows[0] === undefined ? scheduleStoredFailure(options, "resume", "returned", "unknown", "row", "absent")
        : scheduleFromRow(updated.rows[0], options, "resume", "returned", "unknown");
    } catch (cause) { return err(postgreSqlPersistenceOperationError("resume_schedule", cause, options)); }
  });
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
