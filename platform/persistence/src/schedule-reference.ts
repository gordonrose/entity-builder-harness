import { currentOutboxMessageVersion, outboxEntryId } from "@kanbien/core/persistence";
import type { QueueMessage, QueueMessageType } from "@kanbien/core/queues";
import { entityId, isoDateTime, uuid, type ISODateTime, type Result } from "@kanbien/core/shared";
import type { PlatformJobName } from "@kanbien/platform-contracts";
import type { PlatformOutboxStore } from "./outbox";
import type { PlatformSchedule, PlatformScheduleStore } from "./scheduling";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";
import { capturePlatformPersistenceDiagnostic, observePlatformPersistenceDiagnostic,
  persistenceScheduleDeliveryReferenceDiagnosticRecord, type PersistenceScheduleDeliveryReferenceDetail,
  type PlatformPersistenceDiagnosticOptions } from "./diagnostics";

export interface PlatformScheduleDeliveryReferenceOptions extends PlatformPersistenceDiagnosticOptions {
  readonly outbox: Pick<PlatformOutboxStore, "get">;
  readonly schedules: Pick<PlatformScheduleStore, "get">;
  readonly jobName: PlatformJobName;
  readonly messageType: QueueMessageType;
  readonly asOf: ISODateTime;
}

/** Queue data identifies an outbox entry, never an application mutation target. */
export async function loadPlatformScheduleDelivery(message: QueueMessage,
  options: PlatformScheduleDeliveryReferenceOptions): Promise<Result<PlatformSchedule, PlatformPersistenceError>> {
  const reject = (field: PersistenceScheduleDeliveryReferenceDetail["field"], reason: PersistenceScheduleDeliveryReferenceDetail["reason"]) => {
    const diagnosticRecord = capturePlatformPersistenceDiagnostic(() => persistenceScheduleDeliveryReferenceDiagnosticRecord(field, reason));
    observePlatformPersistenceDiagnostic(options, diagnosticRecord);
    return { ok: false as const, error: platformPersistenceError({ code: "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID",
      defaultMessage: "Scheduled delivery does not match its durable reference.", diagnosticRecord }) };
  };
  const payload = message.payload;
  if (payload === null || typeof payload !== "object" || Array.isArray(payload)) return reject("payload", "wrong-type");
  const id = (payload as Record<string, unknown>).outboxEntryId;
  if (id === undefined) return reject("outbox-id", "missing");
  if (typeof id !== "string") return reject("outbox-id", "wrong-type");
  if (id.length === 0) return reject("outbox-id", "empty");
  if (message.id !== id || message.idempotencyKey !== id) return reject("outbox-id", "mismatch");
  if (message.type !== options.messageType) return reject("message-type", "mismatch");
  if (message.version !== Number(currentOutboxMessageVersion)) return reject("message-version", "mismatch");
  const asOf = isoDateTime(options.asOf);
  if (!asOf.ok) return reject("as-of", "invalid-format");
  const outbox = await options.outbox.get(outboxEntryId(id));
  if (outbox === null) return reject("outbox", "not-found");
  if (outbox.entry.id !== id) return reject("outbox-id", "mismatch");
  if (String(outbox.entry.messageType) !== String(options.messageType)) return reject("message-type", "mismatch");
  if (outbox.entry.messageVersion !== currentOutboxMessageVersion) return reject("message-version", "mismatch");
  if (outbox.entry.tenantId !== message.tenantId) return reject("tenant", "mismatch");
  if (outbox.entry.subject.kind !== "platform.schedule") return reject("schedule-reference", "mismatch");
  const scheduleId = uuid(outbox.entry.subject.id);
  if (!scheduleId.ok) return reject("schedule-reference", "invalid-format");
  const schedule = await options.schedules.get(entityId<"PlatformScheduleId">(scheduleId.value));
  if (schedule === null) return reject("schedule", "not-found");
  if (schedule.id !== entityId<"PlatformScheduleId">(scheduleId.value)) return reject("schedule-reference", "mismatch");
  if (schedule.jobName !== options.jobName) return reject("job", "mismatch");
  if (schedule.state !== "delivery-created" || schedule.outboxEntryId !== id) return reject("handoff", "mismatch");
  const dueAt = isoDateTime(schedule.dueAt);
  if (!dueAt.ok) return reject("due-at", "invalid-format");
  if (Date.parse(asOf.value) < Date.parse(dueAt.value)) return reject("schedule", "not-due");
  return { ok: true, value: schedule };
}
