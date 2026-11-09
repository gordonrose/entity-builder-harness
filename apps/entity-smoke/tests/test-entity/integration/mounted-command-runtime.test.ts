import { deepEqual, equal, rejects } from "node:assert/strict";
import { recordConfigSource } from "@kanbien/core/config";
import { createDiagnosticRecord, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { noopLogger } from "@kanbien/core/logging";
import { noopMetrics } from "@kanbien/core/monitoring";
import { recordLifecyclePolicy, recordRetentionPolicyReference } from "@kanbien/core/persistence";
import { coreUuidDiagnostic, coreUuidGenerationDiagnostic, correlationId, fixedClock,
  isoDateTimeFromDate, ok, uuid } from "@kanbien/core/shared";
import { fixedFeatureFlagReader, validatePlatformCapabilityObservabilityProfile,
  validatePlatformDiagnosticCatalog, validatePlatformRouteRegistration,
  type PlatformAppRegistry, type PlatformCapabilityObservabilityProfile, type PlatformDiagnosticCatalog,
  type PlatformHealthRegistration, type PlatformMountDeps, type PlatformRequestContext,
  type PlatformRouteRegistration } from "@kanbien/platform-contracts";
import { createEntitySmokePersistenceApp, inMemoryTestEntityRepository, testEntityDiagnosticCatalog,
  type CreateTestEntityInput, type EntitySmokePersistenceAppOptions, type TestEntityError,
  type TestEntityServiceDependencies } from "../../../src/index";

async function main(): Promise<void> {
  const canary = "synthetic-private-command-error";
  const now = new Date("2026-11-09T01:00:00Z");
  const clock = fixedClock(now);
  const id = uuid("a0b1c2d3-e4f5-4a67-8b90-123456789abc");
  const reference = recordRetentionPolicyReference("test-entity.retention");
  if (!id.ok || !reference.ok) throw new Error("Expected valid fixture identifiers.");
  const policy = recordLifecyclePolicy({ recoveryWindowMs: 60_000, retentionPolicy: reference.value, legalHoldCheckRequired: true });
  const primary = createDiagnosticRecord(coreUuidGenerationDiagnostic, { reason: "generated-value-invalid" });
  const companion = createDiagnosticRecord(coreUuidDiagnostic, { reason: "invalid-format" });
  if (!policy.ok || !primary.ok || !companion.ok) throw new Error("Expected valid fixture contracts.");
  const related = [companion.value];
  const generationFailure = { code: "UUID_GENERATION_FAILED", defaultMessage: "The system could not generate a UUID.",
    diagnosticRecord: primary.value, relatedDiagnosticRecords: related, cause: new Error(canary) };
  let generated = 0;
  let repositoryCalls = 0;
  let createFailure: TestEntityError | undefined;
  let readFailure: TestEntityError | undefined;
  let generationFails = false;
  const repository = inMemoryTestEntityRepository();
  const services: TestEntityServiceDependencies = {
    clock, lifecyclePolicy: policy.value,
    uuidGenerator: { generate() { generated++; return generationFails ? { ok: false, error: generationFailure } : id; } },
    repository: {
      async create(entity) { repositoryCalls++; return createFailure === undefined ? repository.create(entity) : { ok: false, error: createFailure }; },
      get(entityId) { repositoryCalls++; if (readFailure !== undefined) throw readFailure; return repository.get(entityId); },
      save(entity) { repositoryCalls++; return repository.save(entity); },
      listByStatus(status) { repositoryCalls++; if (readFailure !== undefined) throw readFailure; return repository.listByStatus(status); },
    },
  };
  const catalogs: PlatformDiagnosticCatalog[] = [];
  const profiles: PlatformCapabilityObservabilityProfile[] = [];
  const routes: PlatformRouteRegistration[] = [];
  const health: PlatformHealthRegistration[] = [];
  const unexpectedRegistration = (): never => { throw new Error("Unexpected registration outside this smoke mount."); };
  // A recording dependency seam, not a second Platform registry implementation.
  const registry: PlatformAppRegistry = {
    registerDiagnosticCatalog(catalog) {
      const checked = validatePlatformDiagnosticCatalog(catalog, catalogs);
      if (!checked.ok) return checked;
      catalogs.push(catalog); return ok(undefined);
    },
    registerObservabilityProfile(profile) {
      const checked = validatePlatformCapabilityObservabilityProfile(profile);
      if (checked.ok) profiles.push(profile);
      return checked;
    },
    registerRoute(route) {
      const checked = validatePlatformRouteRegistration(route);
      if (checked.ok) routes.push(route);
      return checked;
    },
    registerHealthCheck(check) { health.push(check); return ok(undefined); },
    registerPermission: unexpectedRegistration, registerJob: unexpectedRegistration, registerConfigSchema: unexpectedRegistration,
  };
  const mountDeps: PlatformMountDeps = { clock, logger: noopLogger, metrics: noopMetrics,
    config: recordConfigSource({}), flags: fixedFeatureFlagReader({}) };
  let readinessCalls = 0;
  let closeCalls = 0;
  let observation: Awaited<ReturnType<EntitySmokePersistenceAppOptions["readiness"]>> = { readiness: "ready" };
  const app = createEntitySmokePersistenceApp({ services,
    readiness: async () => { readinessCalls++; return observation; }, close: async () => { closeCalls++; } });
  await app.mount(registry, mountDeps);
  equal(app.id, "entity-smoke");
  deepEqual(catalogs, [testEntityDiagnosticCatalog]);
  equal(catalogs[0], testEntityDiagnosticCatalog);
  equal(profiles.length, 1);
  equal(profiles[0]!.name, "entity-smoke.test-entity.commands");
  equal(profiles[0]!.capability, "entity-smoke.test-entity"); equal(profiles[0]!.action, "verify");
  deepEqual(profiles[0]!.signals, ["operational_log"]);
  deepEqual(profiles[0]!.logFieldNames, ["capability", "action", "outcome", "error_class"]);
  deepEqual(profiles[0]!.errorClasses, ["test_entity_operation_failed", "test_entity_request_invalid"]);
  equal(routes.length, 1); equal(health.length, 1);
  const route = routes[0]!;
  equal(route.name, "entity-smoke.test-entity.command"); equal(route.method, "POST");
  equal(route.path, "/entity-smoke/test-entity"); deepEqual(route.auth, { kind: "public" });
  deepEqual(route.observability, { kind: "profile", profile: profiles[0]!.name });
  const context: PlatformRequestContext = { ...mountDeps, correlationId: correlationId("fixture-command"),
    requestId: correlationId("fixture-request"), now: isoDateTimeFromDate(now), method: "POST", path: route.path };
  const command = (body: unknown, onDiagnostic?: (record: DiagnosticRecord) => unknown) => route.handler.handle(
    { body, params: {}, query: {}, headers: {} }, { ...context, ...(onDiagnostic === undefined ? {} : { onDiagnostic }) });
  const input: CreateTestEntityInput = { integerValue: 7, uuidValue: id.value, occurredAt: now.toISOString(),
    label: "Example", status: "draft", enabled: true, categories: ["alpha"], notes: ["note"],
    description: null, reviewedAt: null, secondaryCategories: null };

  for (const [invalid, field, reason] of [[null, "input", "invalid-value"],
    [{ action: "create", input: { ...input, uuidValue: canary } }, "uuidValue", "invalid-format"],
    [{ action: "list", status: canary }, "status", "invalid-value"],
    [{ action: "get", id: canary }, "input", "invalid-value"],
    [{ action: "purge", id: id.value }, "input", "invalid-value"],
    [{ action: "assess-purge", id: id.value, retentionSatisfied: true, legalHold: canary }, "input", "invalid-value"]] as const) {
    const response = await command(invalid);
    equal(response.status, 400, "reject invalid command before all feature effects");
    deepEqual(response.body, { error: { code: "TEST_ENTITY_INVALID_INPUT" } });
    deepEqual(response.observability?.diagnosticRecord, { schema: "core/diagnostic-record/v1",
      code: "entity-smoke.test-entity.validation-failed", definitionVersion: 1, detail: { field, reason } });
    equal(JSON.stringify(response).includes(canary), false);
  }
  equal(generated, 0); equal(repositoryCalls, 0);

  const missing = await command({ action: "assess-purge", id: id.value, retentionSatisfied: true, legalHold: false });
  equal(missing.status, 404, "missing entity must not masquerade as successful eligibility assessment");
  deepEqual(missing.body, { error: { code: "TEST_ENTITY_NOT_FOUND", message: "The test entity was not found." } });
  equal(repositoryCalls, 1);
  const created = await command({ action: "create", input });
  equal(created.status, 201);
  const get = await command({ action: "get", id: id.value });
  equal(get.status, 200); deepEqual(get.body, created.body);
  const collision = await command({ action: "create", input: { ...input, label: "must not overwrite" } });
  equal(collision.status, 409);
  equal(collision.observability?.diagnosticRecord?.code, "entity-smoke.test-entity.identifier-conflict");
  deepEqual((await command({ action: "get", id: id.value })).body, created.body);
  const eligible = await command({ action: "assess-purge", id: id.value, retentionSatisfied: true, legalHold: false });
  equal(eligible.status, 200); deepEqual(eligible.body, { eligibility: "not-deleted" });

  createFailure = { code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: "The store operation failed." };
  const beforeProvider = repositoryCalls;
  const unavailable = await command({ action: "create", input });
  equal(unavailable.status, 503); deepEqual(unavailable.body, { error: { code: createFailure.code, message: createFailure.defaultMessage } });
  equal(repositoryCalls, beforeProvider + 1, "returned provider failure is never replayed");
  readFailure = createFailure;
  for (const read of [{ action: "get", id: id.value }, { action: "list", status: "draft" }]) {
    const beforeRead: number = repositoryCalls;
    await rejects(async () => command(read), error => error === readFailure,
      "read/list keep the original dependency throw for the platform boundary");
    equal(repositoryCalls, beforeRead + 1, "dependency read failure is never replayed");
  }
  readFailure = undefined;
  createFailure = undefined;

  generationFails = true;
  const beforeGeneration = generated;
  const beforeRejectedWrite = repositoryCalls;
  const received: DiagnosticRecord[] = [];
  const rejectedSinkRecords: DiagnosticRecord[] = [];
  const expectedBody = { error: { code: "TEST_ENTITY_ID_GENERATION_FAILED", message: "A test entity ID could not be created." } };
  for (const sink of [undefined, (record: DiagnosticRecord) => { received.push(record); },
    (record: DiagnosticRecord) => { rejectedSinkRecords.push(record); throw new Error(canary); },
    (record: DiagnosticRecord) => { rejectedSinkRecords.push(record); return Promise.reject(new Error(canary)); }]) {
    const response = await command({ action: "create", input }, sink);
    equal(response.status, 500); deepEqual(response.body, expectedBody);
    equal(response.observability?.diagnosticRecord, primary.value, "mount preserves the selected source primary");
    equal(JSON.stringify(response.body).includes("diagnostic"), false, "internal records never enter the HTTP body");
    equal(JSON.stringify(response).includes(canary), false, "native cause never enters the response envelope");
  }
  deepEqual(received, [companion.value]); equal(received[0], companion.value, "request callback receives the original companion");
  deepEqual(rejectedSinkRecords, [companion.value, companion.value], "both rejecting sinks are actually invoked");
  equal(rejectedSinkRecords[0], companion.value); equal(rejectedSinkRecords[1], companion.value);
  equal(generated, beforeGeneration + 4, "reporter absence/failure cannot replay the operation");
  equal(repositoryCalls, beforeRejectedWrite, "failed identity never reaches persistence");
  await new Promise<void>(resolve => setImmediate(resolve));

  const healthy = await health[0]!.check.check();
  equal(healthy.status, "healthy"); equal(readinessCalls, 1);
  observation = { readiness: "not-ready", diagnosticRecord: primary.value, relatedDiagnosticRecords: related };
  const unhealthy = await health[0]!.check.check();
  equal(unhealthy.status, "unhealthy"); equal(Reflect.get(unhealthy, "diagnosticRecord"), primary.value);
  equal(Reflect.get(unhealthy, "relatedDiagnosticRecords"), related); equal(readinessCalls, 2);
  const registrationFailure = { code: "PLATFORM_CONTRACT_DUPLICATE_REGISTRATION" as const,
    defaultMessage: "The registration already exists.", diagnosticRecord: primary.value, relatedDiagnosticRecords: related };
  const registrationOrder = ["catalog", "profile", "health", "route"] as const;
  for (const [index, failedAt] of registrationOrder.entries()) {
    const attempted: string[] = [];
    const register = (name: string): ReturnType<PlatformAppRegistry["registerRoute"]> => {
      attempted.push(name);
      return name === failedAt ? { ok: false, error: registrationFailure } : ok(undefined);
    };
    await rejects(async () => app.mount({ ...registry,
      registerDiagnosticCatalog: () => register("catalog"), registerObservabilityProfile: () => register("profile"),
      registerHealthCheck: () => register("health"), registerRoute: () => register("route"),
    }, mountDeps), error => error === registrationFailure);
    deepEqual(attempted, registrationOrder.slice(0, index + 1), "registration rejection stops later registrations");
  }
  await app.lifecycle?.beforeStop?.(); equal(closeCalls, 1, "close delegates exactly once");
  console.log("entity-smoke public mounted-command and health tests passed (recording registry/in-memory dependencies only).");
}

main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
