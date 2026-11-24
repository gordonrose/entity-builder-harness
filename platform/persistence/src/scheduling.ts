import {
  entityId,
  err,
  isoDateTime,
  ok,
  type EntityId,
  type ISODateTime,
  type Result,
  type UuidGenerator,
} from "@kanbien/core/shared";
import type { OutboxEntry, OutboxEntryId } from "@kanbien/core/persistence";
import type { PlatformJobName } from "@kanbien/platform-contracts";
import { persistenceScheduleRejectionDiagnosticRecord } from "./diagnostics";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import { platformOutboxRecord, type PlatformOutboxRecord } from "./types";

/** A stable reference to one instruction to deliver a registered job later. */
export type PlatformScheduleId = EntityId<"PlatformScheduleId">;

/** A reminder either still waits for its due time or has one outbox record. */
export type PlatformScheduleState = "waiting" | "delivery-created";

export interface PlatformSchedule {
  readonly id: PlatformScheduleId;
  readonly jobName: PlatformJobName;
  readonly dueAt: ISODateTime;
  readonly state: PlatformScheduleState;
  /** Present only after the reminder has been handed to the outbox. */
  readonly outboxEntryId?: OutboxEntryId;
}

export type PlatformScheduleHandover =
  | { readonly disposition: "outbox-created"; readonly schedule: PlatformSchedule; readonly outbox: PlatformOutboxRecord }
  | { readonly disposition: "outbox-already-created"; readonly schedule: PlatformSchedule }
  | { readonly disposition: "not-due"; readonly schedule: PlatformSchedule };

/**
 * Creates one future instruction. The caller supplies a registered job name;
 * Core owns UUID creation and UTC normalisation of the supplied due time.
 */
export function createPlatformSchedule(input: {
  readonly jobName: PlatformJobName;
  readonly dueAt: string;
}, uuidGenerator: UuidGenerator): Result<PlatformSchedule> {
  const dueAt = isoDateTime(input.dueAt);
  if (!dueAt.ok) return dueAt;

  const generatedId = uuidGenerator.generate();
  if (!generatedId.ok) return generatedId;

  return ok({
    id: entityId<"PlatformScheduleId">(generatedId.value),
    jobName: input.jobName,
    dueAt: dueAt.value,
    state: "waiting",
  });
}

/**
 * A local proof store for schedule-record behaviour. It is intentionally not
 * durable and must not be used as evidence of a database-backed scheduler.
 */
export interface PlatformScheduleStore {
  create(schedule: PlatformSchedule): Promise<Result<PlatformSchedule, PlatformPersistenceError>>;
  get(id: PlatformScheduleId): Promise<PlatformSchedule | null>;
  listDue(input: { readonly asOf: ISODateTime; readonly limit: number }): Promise<Result<readonly PlatformSchedule[], PlatformPersistenceError>>;
  /**
   * Make the durable handoff once. The future due-runner supplies an outbox
   * entry after resolving this schedule's already-registered job; this store
   * makes the entry and schedule-state change one operation.
   */
  handoverDue(input: {
    readonly scheduleId: PlatformScheduleId;
    readonly asOf: ISODateTime;
    readonly outboxEntry: OutboxEntry;
  }): Promise<Result<PlatformScheduleHandover, PlatformPersistenceError>>;
}

export function createInMemoryPlatformScheduleStore(): PlatformScheduleStore {
  const schedules = new Map<PlatformScheduleId, PlatformSchedule>();
  const outbox = new Map<OutboxEntryId, PlatformOutboxRecord>();

  return {
    async create(schedule) {
      if (schedules.has(schedule.id)) {
        return err(platformPersistenceError({
          code: "PLATFORM_PERSISTENCE_DUPLICATE_SCHEDULE",
          defaultMessage: "Schedule already exists.",
          messageKey: "platform.persistence.schedule.duplicate",
          diagnosticRecord: persistenceScheduleRejectionDiagnosticRecord({
            operation: "create",
            field: "id",
            condition: "duplicate",
            effect: "local-state-unchanged",
          }),
        }));
      }

      const stored = copyPlatformSchedule(schedule);
      schedules.set(stored.id, stored);
      return ok(copyPlatformSchedule(stored));
    },

    async get(id) {
      const schedule = schedules.get(id);
      return schedule === undefined ? null : copyPlatformSchedule(schedule);
    },

    async listDue({ asOf, limit }) {
      if (!Number.isInteger(limit) || limit <= 0 || limit > 100) {
        return err(platformPersistenceError({
          code: "PLATFORM_PERSISTENCE_INVALID_LIMIT",
          defaultMessage: "Schedule delivery limit must be an integer between 1 and 100.",
          messageKey: "platform.persistence.schedule.limit.invalid",
          diagnosticRecord: persistenceScheduleRejectionDiagnosticRecord({
            operation: "list-due", field: "limit", condition: !Number.isInteger(limit) ? "not-integer" : limit <= 0 ? "not-positive" : "too-large",
            effect: "local-state-unchanged",
          }),
        }));
      }
      return ok([...schedules.values()]
        .filter(schedule => schedule.state === "waiting" && Date.parse(schedule.dueAt) <= Date.parse(asOf))
        .sort((left, right) => Date.parse(left.dueAt) - Date.parse(right.dueAt) || String(left.id).localeCompare(String(right.id)))
        .slice(0, limit)
        .map(copyPlatformSchedule));
    },

    async handoverDue({ scheduleId, asOf, outboxEntry }) {
      const schedule = schedules.get(scheduleId);
      if (schedule === undefined) return err(platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_SCHEDULE_NOT_FOUND",
        defaultMessage: "Schedule was not found.",
        messageKey: "platform.persistence.schedule.not_found",
        diagnosticRecord: persistenceScheduleRejectionDiagnosticRecord({ operation: "handover", field: "schedule", condition: "not-found", effect: "local-state-unchanged" }),
      }));
      if (schedule.state === "delivery-created") return ok({ disposition: "outbox-already-created", schedule: copyPlatformSchedule(schedule) });
      if (Date.parse(schedule.dueAt) > Date.parse(asOf)) return ok({ disposition: "not-due", schedule: copyPlatformSchedule(schedule) });
      if (outbox.has(outboxEntry.id)) return err(platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY",
        defaultMessage: "Outbox entry already exists.",
        messageKey: "platform.persistence.outbox.duplicate",
        diagnosticRecord: persistenceScheduleRejectionDiagnosticRecord({ operation: "handover", field: "outbox-entry", condition: "duplicate", effect: "local-state-unchanged" }),
      }));
      const delivered = platformOutboxRecord({ entry: outboxEntry });
      const handedOver: PlatformSchedule = { ...schedule, state: "delivery-created", outboxEntryId: outboxEntry.id };
      // These two maps model the same all-or-nothing database transaction.
      outbox.set(outboxEntry.id, delivered);
      schedules.set(scheduleId, handedOver);
      return ok({ disposition: "outbox-created", schedule: copyPlatformSchedule(handedOver), outbox: copyOutboxRecord(delivered) });
    },
  };
}

function copyPlatformSchedule(schedule: PlatformSchedule): PlatformSchedule {
  return { ...schedule };
}

function copyOutboxRecord(record: PlatformOutboxRecord): PlatformOutboxRecord {
  return { ...record, entry: { ...record.entry, subject: { ...record.entry.subject } },
    ...(record.lease === undefined ? {} : { lease: { ...record.lease } }) };
}
