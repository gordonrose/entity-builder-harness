import { deepEqual, equal, rejects } from "node:assert/strict";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { outboxDeliveryPolicy, outboxEntry, outboxEntryId, outboxMessageType, recordId, recordKind, recordReference } from "@kanbien/core/persistence";
import { queueIdempotencyKey, queueMessage, queueMessageId, queueMessageType, queueMessageVersion, type QueueMessage } from "@kanbien/core/queues";
import { entityId, isoDateTimeFromDate, uuid, type ISODateTime, type Result } from "@kanbien/core/shared";
import { tenantId } from "@kanbien/core/tenancy";
import { platformJobName } from "@kanbien/platform-contracts";
import { createPlatformSchedule, loadPlatformScheduleDelivery, platformOutboxRecord, persistenceScheduleRejectionDiagnosticRecord,
  type PlatformOutboxRecord, type PlatformSchedule, type PlatformScheduleDeliveryReferenceOptions } from "../../src/index";
import { withDiagnosticDeliverySuppressed } from "../../../../packages/core/tests/diagnostics/helpers/diagnostic-delivery-fixture";

const canary = "PRIVATE-REFERENCE-FIXTURE-DO-NOT-REPORT";
const code = "persistence.schedule-delivery-reference-rejected";
const instant = isoDateTimeFromDate(new Date("2026-11-26T12:00:00.000Z"));
const jobName = required(platformJobName("fixture.cleanup.run"));
const messageType = required(queueMessageType("fixture.cleanup.requested"));
const id = outboxEntryId("fixture.schedule.delivery");
const initial = required(createPlatformSchedule({ jobName, dueAt: instant }, {
  generate: () => uuid("25d537eb-e590-488c-97ef-a894299ed30e"),
}));
const schedule: PlatformSchedule = { ...initial, state: "delivery-created", outboxEntryId: id };
const entry = outboxEntry({ id, createdAt: instant,
  subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(schedule.id)) }),
  messageType: required(outboxMessageType(String(messageType))), deliveryPolicy: required(outboxDeliveryPolicy("fixture.delivery.v1")) });
const outbox = platformOutboxRecord({ entry });
const message = queueMessage({ id: queueMessageId(String(id)), type: messageType, enqueuedAt: instant,
  idempotencyKey: queueIdempotencyKey(String(id)), payload: { outboxEntryId: String(id) } });

interface Case {
  readonly field: string;
  readonly reason: string;
  readonly reads: readonly [number, number];
  readonly message?: QueueMessage;
  readonly outbox?: PlatformOutboxRecord | null;
  readonly schedule?: PlatformSchedule | null;
  readonly asOf?: ISODateTime;
}

function fixture() {
  const records: { outbox: PlatformOutboxRecord | null; schedule: PlatformSchedule | null } = { outbox, schedule };
  const calls = [0, 0];
  const options: PlatformScheduleDeliveryReferenceOptions = { jobName, messageType, asOf: instant,
    outbox: { get: async selected => { calls[0] = calls[0]! + 1; equal(selected, id); return records.outbox; } },
    schedules: { get: async selected => { calls[1] = calls[1]! + 1; equal(selected, schedule.id); return records.schedule; } } };
  return { records, calls, options };
}

async function main(): Promise<void> {
  const cases: Case[] = [
    ...[null, [], 7, canary].map(payload => ({ field: "payload", reason: "wrong-type", reads: [0, 0] as const,
      message: { ...message, payload } as unknown as QueueMessage })),
    ...[[{}, "missing"], [{ outboxEntryId: 7 }, "wrong-type"], [{ outboxEntryId: "" }, "empty"], [{ outboxEntryId: canary }, "mismatch"]].map(([payload, reason]) => ({
      field: "outbox-id", reason: String(reason), reads: [0, 0] as const, message: { ...message, payload } as unknown as QueueMessage })),
    ...[{ id: queueMessageId("other") }, { idempotencyKey: undefined }, { idempotencyKey: queueIdempotencyKey("other") }].map(changes => ({
      field: "outbox-id", reason: "mismatch", reads: [0, 0] as const, message: { ...message, ...changes } as QueueMessage })),
    { field: "message-type", reason: "mismatch", reads: [0, 0], message: { ...message, type: required(queueMessageType("other.job")) } },
    { field: "message-version", reason: "mismatch", reads: [0, 0], message: { ...message, version: required(queueMessageVersion(2)) } },
    { field: "as-of", reason: "invalid-format", reads: [0, 0], asOf: canary as ISODateTime },
    { field: "outbox", reason: "not-found", reads: [1, 0], outbox: null },
    { field: "outbox-id", reason: "mismatch", reads: [1, 0], outbox: { ...outbox, entry: { ...entry, id: outboxEntryId("other") } } },
    { field: "message-type", reason: "mismatch", reads: [1, 0], outbox: { ...outbox, entry: { ...entry, messageType: required(outboxMessageType("other.job")) } } },
    { field: "message-version", reason: "mismatch", reads: [1, 0], outbox: { ...outbox, entry: { ...entry, messageVersion: 2 } } as PlatformOutboxRecord },
    { field: "tenant", reason: "mismatch", reads: [1, 0], message: { ...message, tenantId: tenantId("tenant-a") } },
    { field: "tenant", reason: "mismatch", reads: [1, 0], outbox: { ...outbox, entry: { ...entry, tenantId: tenantId("tenant-a") } } },
    { field: "tenant", reason: "mismatch", reads: [1, 0], message: { ...message, tenantId: tenantId("tenant-b") }, outbox: { ...outbox, entry: { ...entry, tenantId: tenantId("tenant-a") } } },
    { field: "schedule-reference", reason: "mismatch", reads: [1, 0], outbox: { ...outbox, entry: { ...entry,
      subject: { ...entry.subject, kind: required(recordKind("other.feature")) } } } },
    { field: "schedule-reference", reason: "invalid-format", reads: [1, 0], outbox: { ...outbox, entry: { ...entry,
      subject: { ...entry.subject, id: required(recordId(canary)) } } } },
    { field: "schedule", reason: "not-found", reads: [1, 1], schedule: null },
    { field: "schedule-reference", reason: "mismatch", reads: [1, 1], schedule: { ...schedule, id: entityId<"PlatformScheduleId">("35d537eb-e590-488c-97ef-a894299ed30e") } },
    { field: "job", reason: "mismatch", reads: [1, 1], schedule: { ...schedule, jobName: required(platformJobName("other.feature.job")) } },
    { field: "handoff", reason: "mismatch", reads: [1, 1], schedule: initial },
    { field: "handoff", reason: "mismatch", reads: [1, 1], schedule: { ...schedule, outboxEntryId: outboxEntryId("other") } },
    { field: "handoff", reason: "mismatch", reads: [1, 1], schedule: { ...schedule, outboxEntryId: undefined } as unknown as PlatformSchedule },
    { field: "due-at", reason: "invalid-format", reads: [1, 1], schedule: { ...schedule, dueAt: canary as ISODateTime } },
    { field: "schedule", reason: "not-due", reads: [1, 1], asOf: isoDateTimeFromDate(new Date(Date.parse(instant) - 1)) },
  ];
  for (const sample of cases) {
    const test = fixture(), observations: DiagnosticRecord[] = [];
    if ("outbox" in sample) test.records.outbox = sample.outbox!;
    if ("schedule" in sample) test.records.schedule = sample.schedule!;
    const result = await loadPlatformScheduleDelivery(sample.message ?? message, { ...test.options,
      asOf: sample.asOf ?? instant, onDiagnostic: record => observations.push(record) });
    equal(result.ok, false, sample.field); if (result.ok) throw new Error("Expected rejected durable reference.");
    equal(result.error.code, "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID");
    deepEqual(result.error.diagnosticRecord, expected(sample.field, sample.reason));
    deepEqual(observations, [result.error.diagnosticRecord]);
    deepEqual(observations[0], result.error.diagnosticRecord, "selected record content is preserved at its reporting boundary");
    deepEqual(test.calls, sample.reads, "a rejected link prevents later reads and never retries");
    equal(JSON.stringify([observations, result]).includes(canary), false);
  }

  for (const asOf of [instant, "2026-11-26T13:00:00+01:00" as ISODateTime, isoDateTimeFromDate(new Date(Date.parse(instant) + 1))]) {
    const test = fixture();
    const result = await loadPlatformScheduleDelivery(message, { ...test.options, asOf });
    equal(required(result), schedule, "equal instants, offsets and later instants select the same durable schedule");
    deepEqual(test.calls, [1, 1]);
  }
  const tenant = fixture();
  tenant.records.outbox = { ...outbox, entry: { ...entry, tenantId: tenantId("tenant-a") } };
  equal(required(await loadPlatformScheduleDelivery({ ...message, tenantId: tenantId("tenant-a") }, tenant.options)), schedule);
  equal(required(await loadPlatformScheduleDelivery({ ...message, payload: { ...message.payload, entityId: canary } }, fixture().options)), schedule,
    "extra queue data cannot select an application entity");

  await failureIdentity();
  await diagnosticFaults();
  console.log("Schedule delivery reference validation, time/tenant boundaries and diagnostic fault tests passed.");
}

async function failureIdentity(): Promise<void> {
  const primary = persistenceScheduleRejectionDiagnosticRecord({ operation: "list-due", field: "limit", condition: "not-positive", effect: "local-state-unchanged" });
  const companions = Array.from({ length: 8 }, () => primary);
  const failure = Object.freeze({ code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: canary,
    diagnosticRecord: primary, relatedDiagnosticRecords: companions });
  for (const boundary of ["outbox", "schedule"] as const) {
    const test = fixture(); let failures = 0;
    const options = { ...test.options,
      ...(boundary === "outbox" ? { outbox: { get: async () => { failures++; throw failure; } } }
        : { schedules: { get: async () => { failures++; throw failure; } } }) };
    await rejects(() => loadPlatformScheduleDelivery(message, options), cause => cause === failure);
    equal(failures, 1); deepEqual(test.calls, boundary === "outbox" ? [0, 0] : [1, 0]);
    equal(failure.diagnosticRecord, primary); equal(failure.relatedDiagnosticRecords, companions);
  }
}

async function diagnosticFaults(): Promise<void> {
  const invalid = { ...message, payload: null } as unknown as QueueMessage;
  for (const fault of ["absent", "throw", "rejected-promise", "hostile-thenable"] as const) {
    const test = fixture(); let reports = 0;
    const onDiagnostic = () => {
      reports++;
      if (fault === "throw") throw new Error(canary);
      if (fault === "rejected-promise") return Promise.reject(new Error(canary));
      return Object.defineProperty({}, "then", { get() { throw new Error(canary); } });
    };
    const result = await loadPlatformScheduleDelivery(invalid, { ...test.options, ...(fault === "absent" ? {} : { onDiagnostic }) });
    equal(result.ok, false); if (result.ok) throw new Error("Expected invalid payload.");
    deepEqual(result.error.diagnosticRecord, expected("payload", "wrong-type"));
    deepEqual(test.calls, [0, 0]); equal(reports, fault === "absent" ? 0 : 1);
  }
  await new Promise<void>(resolve => setImmediate(resolve));

  const owner = require("../../src/diagnostics") as typeof import("../../src/diagnostics");
  const original = owner.persistenceScheduleDeliveryReferenceDiagnosticRecord;
  try {
    for (const fault of ["throw", "absent", "malformed"] as const) {
      let builds = 0;
      owner.persistenceScheduleDeliveryReferenceDiagnosticRecord = (() => {
        builds++; if (fault === "throw") throw new Error(canary);
        return fault === "absent" ? undefined : { schema: "invalid", code: canary };
      }) as unknown as typeof original;
      const test = fixture(), observations: DiagnosticRecord[] = [];
      const result = await loadPlatformScheduleDelivery(invalid, { ...test.options, onDiagnostic: record => observations.push(record) });
      equal(result.ok, false); if (result.ok) throw new Error("A broken diagnostic cannot accept work.");
      equal(result.error.diagnosticRecord?.code, "core.diagnostics.processing-failed");
      equal(builds, 1); deepEqual(test.calls, [0, 0]);
      equal(JSON.stringify([result, observations]).includes(canary), false);
    }
  } finally { owner.persistenceScheduleDeliveryReferenceDiagnosticRecord = original; }

  let pending: ReturnType<typeof loadPlatformScheduleDelivery> | undefined;
  const test = fixture(); let suppressed = 0;
  withDiagnosticDeliverySuppressed(attempted => {
    pending = loadPlatformScheduleDelivery(invalid, { ...test.options, onDiagnostic: () => { suppressed++; } });
    deepEqual(attempted, [expected("payload", "wrong-type")]);
  });
  if (pending === undefined) throw new Error("Missing suppressed-delivery result.");
  equal((await pending).ok, false); equal(suppressed, 0); deepEqual(test.calls, [0, 0]);
}

function expected(field: string, reason: string) {
  return { schema: "core/diagnostic-record/v1", code, definitionVersion: 1,
    detail: { field, reason, effect: "application-work-not-invoked" } };
}

function required<T>(result: Result<T, unknown>): T { if (!result.ok) throw result.error; return result.value; }
main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
