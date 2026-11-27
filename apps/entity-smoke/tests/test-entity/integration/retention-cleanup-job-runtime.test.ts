import { deepEqual, equal, rejects } from "node:assert/strict";
import { outboxDeliveryPolicy, outboxEntry, outboxEntryId, outboxMessageType, recordId, recordKind, recordReference,
  recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { queueIdempotencyKey, queueMessage, queueMessageId, type QueueMessage } from "@kanbien/core/queues";
import { fixedFeatureFlagReader, type PlatformAppRegistry, type PlatformJobRegistration, type PlatformMountDeps } from "@kanbien/platform-contracts";
import { recordConfigSource } from "@kanbien/core/config";
import { noopLogger } from "@kanbien/core/logging";
import { noopMetrics } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate, ok, type Clock, type Result, type UUID, type UuidGenerator } from "@kanbien/core/shared";
import { createInMemoryPlatformScheduleStore, type PlatformSchedule, type PlatformOutboxRecord } from "@kanbien/platform-persistence";
import { archiveTestEntityService, createEntitySmokePersistenceApp, createTestEntityService, deleteTestEntityService,
  entitySmokeExpiredPurgeJobName, entitySmokeExpiredPurgeMessageType, inMemoryTestEntityRepository, purgeExpiredTestEntityService,
  restoreLogicallyDeletedTestEntityService, testEntityExpiredPurgeDueAt, testEntityRetentionWindowMs,
  type CreateTestEntityInput, type TestEntityError, type TestEntityRetentionDelivery, type TestEntityServiceDependencies } from "../../../src/index";

function required<T>(result: Result<T, unknown>): T { if (!result.ok) throw result.error; return result.value; }

async function main(): Promise<void> {
  let now = new Date("2026-11-22T12:00:00.000Z");
  const clock: Clock = { now: () => new Date(now) };
  const lifecyclePolicy = required(recordLifecyclePolicy({ recoveryWindowMs: 60_000,
    retentionPolicy: required(recordRetentionPolicyReference("test-entity.retention")), legalHoldCheckRequired: true }));
  let ordinal = 0;
  const generator: UuidGenerator = { generate: () => ok(`${(++ordinal).toString(16).padStart(8, "0")}-e4f5-4a67-8b90-123456789abc` as UUID) };
  const repository = inMemoryTestEntityRepository();
  const services: TestEntityServiceDependencies = { repository, clock, uuidGenerator: generator, lifecyclePolicy };
  const input: CreateTestEntityInput = { integerValue: 7, uuidValue: "c0b1c2d3-e4f5-4a67-8b90-123456789abc", occurredAt: now.toISOString(),
    label: "Cleanup fixture", status: "draft", enabled: true, categories: ["alpha"], notes: ["fixture"], description: null,
    reviewedAt: null, secondaryCategories: null };
  const selected = required(await createTestEntityService(input, services));
  const unrelated = required(await createTestEntityService({ ...input, label: "Existing unrelated eligible row" }, services));
  const unarchived = required(await createTestEntityService({ ...input, label: "Keep unarchived" }, services));
  required(await archiveTestEntityService(selected.id, services));
  required(await archiveTestEntityService(unrelated.id, services));
  required(await deleteTestEntityService(unrelated.id, services));
  required(await deleteTestEntityService(unarchived.id, services));
  const originalUnrelated = await repository.get(unrelated.id);
  const schedules = createInMemoryPlatformScheduleStore();
  let scheduled: PlatformSchedule | undefined;
  let transactionCalls = 0;
  const reminder = { jobName: entitySmokeExpiredPurgeJobName, store: schedules };
  const durableServices: TestEntityServiceDependencies = { ...services, expiredPurgeReminder: reminder,
    deletionTransaction: { run: operation => { transactionCalls++; return operation({ repository,
      schedules: { create: schedule => { scheduled = schedule; return schedules.create(schedule); } } }); } } };
  const missingTransaction = await deleteTestEntityService(selected.id, { ...services, expiredPurgeReminder: reminder });
  equal(missingTransaction.ok, false);
  if (!missingTransaction.ok) deepEqual(missingTransaction.error.diagnosticRecord?.detail,
    { field: "transaction", reason: "missing", effect: "mutation-not-invoked" });
  equal((await repository.get(selected.id))?.lifecycle.state, "active");
  required(await deleteTestEntityService(selected.id, durableServices));
  equal(transactionCalls, 1);
  if (scheduled === undefined) throw new Error("Expected an atomic reminder.");
  const originalSchedule: PlatformSchedule = scheduled;
  deepEqual(originalSchedule.subject, { kind: "entity-smoke.test-entity", id: selected.id });
  equal(originalSchedule.dueAt, "2026-11-22T12:05:00.001Z");
  const originalDeleted = (await repository.get(selected.id))!;
  if (originalDeleted.lifecycle.state !== "deleted") throw new Error("Expected deletion fixture.");
  const longerRecovery = { ...originalDeleted, lifecycle: { ...originalDeleted.lifecycle,
    restoreEligibleUntil: isoDateTimeFromDate(new Date("2026-11-22T12:10:00.000Z")) } };
  equal(testEntityExpiredPurgeDueAt(longerRecovery)?.toISOString(), "2026-11-22T12:10:00.001Z", "one reminder waits for both periods");
  const longerRepository = inMemoryTestEntityRepository([longerRecovery]);
  const longerSchedule = { ...originalSchedule, dueAt: isoDateTimeFromDate(testEntityExpiredPurgeDueAt(longerRecovery)!) };
  const longerServices = { ...services, repository: longerRepository };
  now = new Date("2026-11-22T12:10:00.000Z");
  deepEqual(required(await purgeExpiredTestEntityService(longerSchedule, longerServices)), { inspected: 1, purged: 0 });
  now = new Date(now.getTime() + 1);
  deepEqual(required(await purgeExpiredTestEntityService(longerSchedule, longerServices)), { inspected: 1, purged: 1 });
  now = new Date("2026-11-22T12:00:00.000Z");

  const entry = outboxEntry({ id: outboxEntryId("retention-fixture-outbox"),
    subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(originalSchedule.id)) }),
    messageType: required(outboxMessageType(String(entitySmokeExpiredPurgeMessageType))),
    deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")), createdAt: originalSchedule.dueAt });
  const handover = required(await schedules.handoverDue({ scheduleId: originalSchedule.id, asOf: originalSchedule.dueAt, outboxEntry: entry }));
  if (handover.disposition !== "outbox-created") throw new Error("Expected handoff.");
  let observedOutbox: PlatformOutboxRecord | null = handover.outbox;
  let observedSchedule: PlatformSchedule | null = handover.schedule;
  const handedSchedule = handover.schedule;
  let outboxReads = 0, scheduleReads = 0, entityReads = 0;
  const delivery: TestEntityRetentionDelivery = {
    outbox: { get: async () => { outboxReads++; return observedOutbox; } },
    schedules: { get: async () => { scheduleReads++; return observedSchedule; } },
  };
  const countedServices = { ...services, repository: { ...repository, get: (id: typeof selected.id) => { entityReads++; return repository.get(id); } } };
  const message = queueMessage({ id: queueMessageId(String(entry.id)), type: entitySmokeExpiredPurgeMessageType,
    enqueuedAt: entry.createdAt, idempotencyKey: queueIdempotencyKey(String(entry.id)), payload: { outboxEntryId: String(entry.id) } });
  const job = await mountedJob(countedServices, delivery);
  equal(job.name, "entity-smoke.test-entity.purge-expired");
  const invoke = (selectedMessage: QueueMessage = message) => Promise.resolve(job.handler.handle(selectedMessage, {} as never));
  const rejected = async (field: string, reason: string, call = () => invoke(), platform = false) => {
    const reads = entityReads;
    await rejects(call, (error: TestEntityError) => {
      equal(error.code, platform ? "PLATFORM_PERSISTENCE_QUEUE_MAPPING_INVALID" : "TEST_ENTITY_RETENTION_REJECTED");
      deepEqual(error.diagnosticRecord, { schema: "core/diagnostic-record/v1",
        code: platform ? "persistence.schedule-delivery-reference-rejected" : "entity-smoke.test-entity.retention-rejected", definitionVersion: 1,
        detail: { field, reason, effect: platform ? "application-work-not-invoked" : "mutation-not-invoked" } });
      equal(JSON.stringify(error).includes("synthetic-private-canary"), false);
      return true;
    });
    equal(entityReads, reads, "invalid delivery must not reach entity storage");
  };
  await rejected("schedule", "not-due", undefined, true);
  now = new Date("2026-11-22T12:05:00.000Z");
  deepEqual(required(await purgeExpiredTestEntityService(handedSchedule, services)), { inspected: 1, purged: 0 }, "strict retention boundary retains the row");
  now = new Date(now.getTime() + 1);
  // Platform owns the exhaustive reference-validation matrix. These mounted
  // cases prove its actual selected diagnostic prevents this feature's mutation.
  await rejected("payload", "wrong-type", () => invoke({ ...message, payload: null } as unknown as QueueMessage), true);
  await rejected("outbox-id", "mismatch", () => invoke({ ...message, payload: { outboxEntryId: "synthetic-private-canary" } }), true);
  observedOutbox = null; await rejected("outbox", "not-found", undefined, true); observedOutbox = handover.outbox;
  observedSchedule = originalSchedule; await rejected("handoff", "mismatch", undefined, true);
  observedSchedule = { ...handedSchedule, subject: undefined } as unknown as PlatformSchedule; await rejected("subject", "missing");
  observedSchedule = { ...handedSchedule, subject: recordReference({ kind: required(recordKind("other.feature")), id: required(recordId(selected.id)) }) };
  await rejected("subject", "mismatch");
  observedSchedule = { ...handedSchedule, subject: recordReference({ kind: required(recordKind("entity-smoke.test-entity")), id: required(recordId("synthetic-private-canary")) }) };
  await rejected("entity-id", "invalid-format"); observedSchedule = handedSchedule;

  const failure: TestEntityError = { code: "CONTROLLED_PURGE_FAILURE", defaultMessage: "Controlled failure." };
  const failedJob = await mountedJob({ ...services, repository: { ...repository, purgeArchivedDeleted: async () => ({ ok: false, error: failure }) } }, delivery);
  await rejects(() => Promise.resolve(failedJob.handler.handle(message, {} as never)), error => error === failure, "failed Result is not worker success");
  const missingDeliveryJob = await mountedJob(services);
  await rejected("delivery", "missing", () => Promise.resolve(missingDeliveryJob.handler.handle(message, {} as never)));
  for (const failedDelivery of [{ ...delivery, outbox: { get: async () => { throw failure; } } },
    { ...delivery, schedules: { get: async () => { throw failure; } } }]) {
    const failedReadJob = await mountedJob(services, failedDelivery);
    await rejects(() => Promise.resolve(failedReadJob.handler.handle(message, {} as never)), error => error === failure,
      "durable metadata failures must not become successful delivery");
  }

  // A restored row and a later deletion generation cannot be purged by the old reminder.
  const deleted = (await repository.get(selected.id))!;
  now = new Date("2026-11-22T12:00:30.000Z");
  required(await restoreLogicallyDeletedTestEntityService(selected.id, services));
  now = new Date("2026-11-22T12:05:00.001Z");
  await invoke(); equal((await repository.get(selected.id))?.lifecycle.state, "active");
  required(await deleteTestEntityService(selected.id, services));
  now = new Date(now.getTime() + testEntityRetentionWindowMs + 1);
  await invoke(); equal((await repository.get(selected.id))?.lifecycle.state, "deleted", "old reminder cannot select a newer deletion");
  required(await repository.save(deleted, (await repository.get(selected.id))!));

  // Simulate a concurrent restore/re-delete after the domain read; storage rechecks generation.
  const concurrent = await mountedJob({ ...services, repository: { ...repository, purgeArchivedDeleted: async condition => {
    if (deleted.lifecycle.state !== "deleted") throw new Error("Expected deleted fixture.");
    required(await repository.save({ ...deleted, lifecycle: { ...deleted.lifecycle, deletedAt: isoDateTimeFromDate(now) } }, deleted));
    return repository.purgeArchivedDeleted(condition);
  } } }, delivery);
  await concurrent.handler.handle(message, {} as never);
  equal(await repository.get(selected.id) !== null, true, "conditional delete does not remove a changed generation");
  required(await repository.save(deleted, (await repository.get(selected.id))!));
  const borrowedDate = new Date(now); let clockReads = 0;
  const changingClockJob = await mountedJob({ ...services, clock: { now: () => { clockReads++; return borrowedDate; } },
    repository: { ...repository, get: async id => { const found = await repository.get(id); borrowedDate.setTime(0); return found; } } }, delivery);
  await changingClockJob.handler.handle(message, {} as never);
  equal(clockReads, 1, "due and retention checks share one defensive clock snapshot");
  equal(await repository.get(selected.id), null);
  await invoke(); equal(await repository.get(selected.id), null, "duplicate delivery is harmless");
  deepEqual(await repository.get(unrelated.id), originalUnrelated, "pre-existing eligible data is untouched");
  equal((await repository.get(unarchived.id))?.visibility, "active", "unarchived deleted row remains");
  equal(outboxReads > 0 && scheduleReads > 0, true);
  console.log("entity-smoke targeted retention and durable metadata job tests passed.");
}

async function mountedJob(services: TestEntityServiceDependencies, retentionDelivery?: TestEntityRetentionDelivery): Promise<PlatformJobRegistration> {
  const jobs: PlatformJobRegistration[] = [];
  const registry: PlatformAppRegistry = { registerJob: job => { jobs.push(job); return ok(undefined); },
    registerDiagnosticCatalog: () => ok(undefined), registerPermission: () => ok(undefined), registerRoute: () => ok(undefined),
    registerObservabilityProfile: () => ok(undefined), registerHealthCheck: () => ok(undefined), registerConfigSchema: () => ok(undefined) };
  const deps: PlatformMountDeps = { clock: services.clock, logger: noopLogger, metrics: noopMetrics, config: recordConfigSource({}), flags: fixedFeatureFlagReader({}) };
  await createEntitySmokePersistenceApp({ services, readiness: async () => ({ readiness: "ready" }), close: async () => undefined,
    ...(retentionDelivery === undefined ? {} : { retentionDelivery }) }).mount(registry, deps);
  equal(jobs.length, 1); return jobs[0]!;
}

main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
