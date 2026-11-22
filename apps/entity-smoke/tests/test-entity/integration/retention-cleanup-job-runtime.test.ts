import { deepEqual, equal } from "node:assert/strict";
import { recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { fixedFeatureFlagReader, type PlatformAppRegistry, type PlatformJobRegistration, type PlatformMountDeps } from "@kanbien/platform-contracts";
import { recordConfigSource } from "@kanbien/core/config";
import { noopLogger } from "@kanbien/core/logging";
import { noopMetrics } from "@kanbien/core/monitoring";
import { ok, type Clock, type UUID, type UuidGenerator } from "@kanbien/core/shared";
import { createInMemoryPlatformScheduleStore, type PlatformSchedule } from "@kanbien/platform-persistence";
import {
  archiveTestEntityService,
  createEntitySmokePersistenceApp,
  createTestEntityService,
  deleteTestEntityService,
  entitySmokeExpiredPurgeJobName,
  inMemoryTestEntityRepository,
  testEntityRetentionWindowMs,
  type CreateTestEntityInput,
  type TestEntityServiceDependencies,
} from "../../../src/index";

async function main(): Promise<void> {
  let now = new Date("2026-11-22T12:00:00.000Z");
  const clock: Clock = { now: () => new Date(now) };
  const policyReference = recordRetentionPolicyReference("test-entity.retention");
  if (!policyReference.ok) throw new Error("Expected retention reference.");
  const lifecyclePolicy = recordLifecyclePolicy({ recoveryWindowMs: 60_000, retentionPolicy: policyReference.value, legalHoldCheckRequired: true });
  if (!lifecyclePolicy.ok) throw new Error("Expected lifecycle policy.");
  const generated = ["a0b1c2d3-e4f5-4a67-8b90-123456789abc", "b0b1c2d3-e4f5-4a67-8b90-123456789abc", "c0b1c2d3-e4f5-4a67-8b90-123456789abc"] as UUID[];
  const generator: UuidGenerator = { generate: () => {
    const next = generated.shift();
    if (next === undefined) throw new Error("No fixture UUID remains.");
    return ok(next);
  } };
  const repository = inMemoryTestEntityRepository();
  const scheduled: PlatformSchedule[] = [];
  const localScheduleStore = createInMemoryPlatformScheduleStore();
  const services: TestEntityServiceDependencies = { repository, clock, uuidGenerator: generator, lifecyclePolicy: lifecyclePolicy.value,
    expiredPurgeReminder: { jobName: entitySmokeExpiredPurgeJobName, store: {
      create: async schedule => { scheduled.push(schedule); return localScheduleStore.create(schedule); },
      get: id => localScheduleStore.get(id),
      listDue: input => localScheduleStore.listDue(input),
      handoverDue: input => localScheduleStore.handoverDue(input),
    } } };
  const input: CreateTestEntityInput = {
    integerValue: 7, uuidValue: "c0b1c2d3-e4f5-4a67-8b90-123456789abc", occurredAt: now.toISOString(), label: "Cleanup fixture",
    status: "draft", enabled: true, categories: ["alpha"], notes: ["fixture"], description: null, reviewedAt: null, secondaryCategories: null,
  };
  const archived = await createTestEntityService(input, services);
  const unarchived = await createTestEntityService({ ...input, label: "Keep fixture" }, services);
  if (!archived.ok || !unarchived.ok) throw new Error("Expected fixture creation.");
  equal((await archiveTestEntityService(archived.value.id, services)).ok, true);
  equal((await deleteTestEntityService(archived.value.id, services)).ok, true);
  equal((await deleteTestEntityService(unarchived.value.id, services)).ok, true);
  deepEqual(scheduled, [{ id: "c0b1c2d3-e4f5-4a67-8b90-123456789abc", jobName: entitySmokeExpiredPurgeJobName,
    dueAt: "2026-11-22T12:05:00.001Z", state: "waiting" }]);

  const jobs: PlatformJobRegistration[] = [];
  const registry: PlatformAppRegistry = {
    registerJob(job) { jobs.push(job); return ok(undefined); },
    registerDiagnosticCatalog: () => ok(undefined), registerPermission: () => ok(undefined), registerRoute: () => ok(undefined),
    registerObservabilityProfile: () => ok(undefined), registerHealthCheck: () => ok(undefined), registerConfigSchema: () => ok(undefined),
  };
  const mountDeps: PlatformMountDeps = { clock, logger: noopLogger, metrics: noopMetrics, config: recordConfigSource({}), flags: fixedFeatureFlagReader({}) };
  await createEntitySmokePersistenceApp({ services, readiness: async () => ({ readiness: "ready" }), close: async () => undefined }).mount(registry, mountDeps);
  equal(jobs.length, 1);
  const job = jobs[0]!;
  equal(job.name, "entity-smoke.test-entity.purge-expired");
  equal(job.messageType, "entity-smoke.test-entity.purge-expired");

  await job.handler.handle({} as never, {} as never);
  equal(await repository.get(archived.value.id) !== null, true, "five minutes has not elapsed");

  now = new Date(now.getTime() + testEntityRetentionWindowMs + 1);
  await job.handler.handle({} as never, {} as never);
  equal(await repository.get(archived.value.id), null, "archived deleted record is purged after five minutes");
  equal((await repository.get(unarchived.value.id))?.visibility, "active", "a deleted but unarchived record is retained");
  deepEqual(await repository.listArchivedDeleted(), []);
  console.log("entity-smoke retention cleanup job test passed.");
}

main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
