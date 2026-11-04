import { deepEqual, equal, notEqual, rejects } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { Permission } from "@kanbien/core/authz";
import { createInMemoryTracer } from "@kanbien/core/monitoring";
import { persistenceError, type Transaction } from "@kanbien/core/persistence";
import { inMemoryQueue, type QueueIdempotencyKey } from "@kanbien/core/queues";
import { causationId, correlationId, err, isoDateTimeFromDate, ok as successful, type Result } from "@kanbien/core/shared";
import type {
  PlatformPersistenceAtomicWriter,
  PlatformPersistenceError,
  PlatformPersistenceMutation,
} from "@kanbien/platform-persistence";
import {
  createInMemoryPlatformOutboxStore,
  createInMemoryPlatformProcessingStore,
  createPlatformOutboxRelay,
  platformPersistenceLeaseOwner,
  type PlatformOutboxQueuePayload,
  type PlatformPersistenceDiagnosticOptions,
  platformPersistenceDiagnosticCatalog,
  platformPersistenceError,
  persistenceLocalRejectionDiagnosticRecord,
  observePlatformPersistenceDiagnostic,
  resolvePlatformPersistenceDiagnosticOptions,
  selectPlatformPersistenceDiagnosticEvidence,
} from "@kanbien/platform-persistence";
import { createPlatformRuntimeRequestContext } from "@kanbien/platform-runtime";
import type { PlatformDiagnosticContext, PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { createPlatformServerShell } from "@kanbien/platform-server";
import {
  createPlatformTestConfigSource,
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  createPlatformTestQueueMessage,
  mountPlatformAppForTest,
  runPlatformTestHealthChecks,
  validatePlatformTestConfigSchemas,
} from "@kanbien/platform-testing";
import {
  createInMemoryPlatformWorkerIdempotencyStore,
  createPlatformWorkerShell,
} from "@kanbien/platform-workers";
import {
  platformSmokeApp,
  platformSmokeAppManifest,
  platformSmokeEchoObservabilityProfileName,
  platformSmokeJobMessageType,
  platformSmokeReadPermission,
  platformSmokeRebuildObservabilityProfileName,
  platformSmokeWorkItemAcceptedJobMessageType,
  platformSmokeWorkItemDeliveryObservabilityProfileName,
  platformSmokeWorkItemCreatePermission,
  acceptPlatformSmokeWorkItem,
  createPlatformSmokeApp,
  platformSmokeWorkItemId,
  type PlatformSmokeWorkItemRepository,
  platformSmokeWorkItemAcceptanceObservabilityProfileName,
} from "../src/index";

async function main(): Promise<void> {
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
  const tracer = createInMemoryTracer();
  const deps = createPlatformTestMountDeps({
    logger,
    metrics,
    config: createPlatformTestConfigSource({ PLATFORM_SMOKE_APP_NAME: "Smoke Test" }),
  });

  const mounted = await mountPlatformAppForTest(platformSmokeApp, { deps });
  equal(mounted.ok, true);
  if (!mounted.ok) {
    throw new Error("Expected platform-smoke app to mount.");
  }
  equal(mounted.value.permissions.length, 1);
  equal(mounted.value.routes.length, 1);
  equal(mounted.value.jobs.length, 2);
  equal(mounted.value.observabilityProfiles.length, 3);
  equal(mounted.value.healthChecks.length, 1);
  equal(mounted.value.configSchemas.length, 1);
  equal(mounted.value.routes[0]?.path, "/smoke/:id");
  equal(mounted.value.jobs[0]?.messageType, platformSmokeJobMessageType);
  equal(mounted.value.jobs[1]?.messageType, platformSmokeWorkItemAcceptedJobMessageType);
  deepEqual(mounted.value.routes[0]?.observability, { kind: "profile", profile: platformSmokeEchoObservabilityProfileName });
  deepEqual(mounted.value.jobs[0]?.observability, { kind: "profile", profile: platformSmokeRebuildObservabilityProfileName });
  deepEqual(mounted.value.jobs[1]?.observability, { kind: "profile", profile: platformSmokeWorkItemDeliveryObservabilityProfileName });
  equal(typeof mounted.value.lifecycle?.beforeStart, "function");

  const config = validatePlatformTestConfigSchemas(mounted.value.configSchemas, deps.config);
  equal(config.ok, true);
  const health = await runPlatformTestHealthChecks(mounted.value.healthChecks);
  equal(health.ok, true);
  if (!health.ok) {
    throw new Error("Expected smoke health to pass.");
  }
  equal(health.value[0]?.status, "healthy");

  const persistedMutations: PlatformPersistenceMutation[] = [];
  const atomicWriter = createRecordingAtomicWriter(persistedMutations);
  let repositoryTransaction: Transaction | undefined;
  const repository: PlatformSmokeWorkItemRepository = {
    async create({ workItem, transaction }) {
      repositoryTransaction = transaction;
      return successful(workItem);
    },
  };
  const workItemId = required(platformSmokeWorkItemId("platform-smoke-work-item-1"));
  const acceptedWorkItem = await acceptPlatformSmokeWorkItem({
    id: workItemId,
    acceptedAt: isoDateTimeFromDate(new Date("2026-09-24T12:00:00.000Z")),
    causationId: causationId("platform-smoke-accept-1"),
  }, { repository, atomicWriter });
  equal(acceptedWorkItem.ok, true);
  if (!acceptedWorkItem.ok) {
    throw new Error("Expected platform-smoke work item acceptance to succeed.");
  }
  equal(repositoryTransaction, atomicWriter.transaction);
  equal(acceptedWorkItem.value.workItem.state, "accepted");
  equal(acceptedWorkItem.value.workItem.revision, 1);
  equal(acceptedWorkItem.value.outboxEntryId, "platform-smoke.work-item-accepted.platform-smoke-work-item-1");
  equal(persistedMutations.length, 1);
  equal(persistedMutations[0]?.recordChange.action, "created");
  equal(persistedMutations[0]?.outboxEntry.messageType, "platform-smoke.work-item.accepted");

  const duplicateMutations: PlatformPersistenceMutation[] = [];
  const duplicateResult = await acceptPlatformSmokeWorkItem({
    id: required(platformSmokeWorkItemId("platform-smoke-work-item-1")),
    acceptedAt: isoDateTimeFromDate(new Date("2026-09-24T12:01:00.000Z")),
    causationId: causationId("platform-smoke-accept-2"),
  }, {
    atomicWriter: createRecordingAtomicWriter(duplicateMutations),
    repository: {
      async create() {
        return err(persistenceError({
          code: "PERSISTENCE_DUPLICATE",
          defaultMessage: "A platform-smoke work item may be accepted once.",
        }));
      },
    },
  });
  equal(duplicateResult.ok, false);
  equal(duplicateMutations.length, 0);

  const routeMutations: PlatformPersistenceMutation[] = [];
  const acceptedRouteIds = new Set<string>();
  const persistenceApp = createPlatformSmokeApp({
    workItemAcceptance: {
      atomicWriter: createRecordingAtomicWriter(routeMutations),
      repository: {
        async create({ workItem }) {
          if (acceptedRouteIds.has(workItem.id)) {
            return err(persistenceError({
              code: "PERSISTENCE_DUPLICATE",
              defaultMessage: "A platform-smoke work item may be accepted once.",
            }));
          }
          acceptedRouteIds.add(workItem.id);
          return successful(workItem);
        },
      },
    },
  });
  const auth = authHookForPermissions([platformSmokeReadPermission, platformSmokeWorkItemCreatePermission]);
  const server = await createPlatformServerShell({
    apps: [persistenceApp],
    deps,
    auth,
    tracer,
    corsAllowlist: ["https://staging.kanbien.example"],
  });
  equal(server.ok, true);
  if (!server.ok) {
    throw new Error("Expected server shell to mount platform-smoke.");
  }
  await server.value.lifecycle.start();

  const unauthenticated = await server.value.handle({ method: "GET", path: "/smoke/abc" });
  equal(unauthenticated.status, 401);
  deepEqual(logger.records().at(-1)?.fields, {
    capability: "platform-smoke.smoke.read",
    action: "read",
    execution_context: "server",
    http_method: "GET",
    http_status_code: 401,
    outcome: "denied",
    error_class: "PLATFORM_SERVER_UNAUTHENTICATED",
  });
  const forbidden = await server.value.handle({
    method: "GET",
    path: "/smoke/abc",
    headers: { authorization: "Bearer no-permission" },
  });
  equal(forbidden.status, 403);
  const ok = await server.value.handle({
    method: "GET",
    path: "/smoke/abc",
    headers: { authorization: "Bearer read", origin: "https://staging.kanbien.example" },
  });
  equal(ok.status, 200);
  deepEqual(ok.body, {
    app: platformSmokeAppManifest.appId,
    appName: "Smoke Test",
    id: "abc",
    ok: true,
  });
  equal(ok.headers["access-control-allow-origin"], "https://staging.kanbien.example");
  equal(metrics.points().some((point) =>
    point.name === "platform.server.request_response_latency"
      && point.labels?.["capability"] === "platform-smoke.smoke.read"
      && point.labels?.["action"] === "read"), true);
  deepEqual(tracer.spans().at(-1)?.end, {
    outcome: "succeeded",
    attributes: {
      capability: "platform-smoke.smoke.read",
      action: "read",
      execution_context: "server",
      http_method: "GET",
      http_status_code: 200,
      outcome: "succeeded",
    },
  });

  const unauthenticatedAcceptance = await server.value.handle({ method: "POST", path: "/smoke/work-items" });
  equal(unauthenticatedAcceptance.status, 401);
  const forbiddenAcceptance = await server.value.handle({
    method: "POST",
    path: "/smoke/work-items",
    headers: { authorization: "Bearer read" },
  });
  equal(forbiddenAcceptance.status, 403);
  const unauthenticatedAdmission = await server.value.handle({ method: "POST", path: "/smoke/work-items/admission" });
  equal(unauthenticatedAdmission.status, 401);
  const forbiddenAdmission = await server.value.handle({
    method: "POST",
    path: "/smoke/work-items/admission",
    headers: { authorization: "Bearer read" },
  });
  equal(forbiddenAdmission.status, 403);
  const admitted = await server.value.handle({
    method: "POST",
    path: "/smoke/work-items/admission",
    headers: { authorization: "Bearer write" },
  });
  equal(admitted.status, 204);
  equal(admitted.body, undefined);
  equal(routeMutations.length, 0);
  equal(metrics.points().some((point) =>
    point.name === "platform.server.request_response_latency"
      && point.labels?.["capability"] === "platform-smoke.persistence.work-item.admission"
      && point.labels?.["action"] === "verify"), true);
  deepEqual(tracer.spans().at(-1)?.end, {
    outcome: "succeeded",
    attributes: {
      capability: "platform-smoke.persistence.work-item.admission",
      action: "verify",
      execution_context: "server",
      http_method: "POST",
      http_status_code: 204,
      outcome: "succeeded",
    },
  });
  const invalidAcceptance = await server.value.handle({
    method: "POST",
    path: "/smoke/work-items",
    requestId: correlationId("3ff5d153-f7eb-4cca-bf68-b38516dbe701"),
    headers: { authorization: "Bearer write" },
    body: {},
  });
  equal(invalidAcceptance.status, 400);
  const acceptedAcceptance = await server.value.handle({
    method: "POST",
    path: "/smoke/work-items",
    requestId: correlationId("3ff5d153-f7eb-4cca-bf68-b38516dbe701"),
    headers: { authorization: "Bearer write" },
  });
  equal(acceptedAcceptance.status, 202);
  deepEqual(acceptedAcceptance.body, {
    workItemId: "3ff5d153-f7eb-4cca-bf68-b38516dbe701",
    status: "accepted",
  });
  equal(routeMutations.length, 1);
  const duplicateAcceptance = await server.value.handle({
    method: "POST",
    path: "/smoke/work-items",
    requestId: correlationId("3ff5d153-f7eb-4cca-bf68-b38516dbe701"),
    headers: { authorization: "Bearer write" },
  });
  equal(duplicateAcceptance.status, 409);
  equal(routeMutations.length, 1);
  equal(metrics.points().some((point) =>
    point.name === "platform.server.request_response_latency"
      && point.labels?.["capability"] === "platform-smoke.persistence.work-item"
      && point.labels?.["action"] === "create"), true);

  const worker = await createPlatformWorkerShell({
    apps: [platformSmokeApp],
    deps,
    idempotency: createInMemoryPlatformWorkerIdempotencyStore(),
  });
  equal(worker.ok, true);
  if (!worker.ok) {
    throw new Error("Expected worker shell to mount platform-smoke.");
  }
  equal((await worker.value.start()).ok, true);

  const message = {
    ...createPlatformTestQueueMessage({
      id: "platform-smoke-rebuild-1",
      type: platformSmokeJobMessageType,
      payload: { rebuild: true },
    }),
    idempotencyKey: "platform-smoke-rebuild-1" as QueueIdempotencyKey,
  };
  equal(worker.value.enqueue(message).ok, true);
  const job = await worker.value.runNext();
  equal(job.ok, true);
  if (!job.ok || job.value.status !== "succeeded") {
    throw new Error("Expected platform-smoke job to succeed.");
  }
  equal(job.value.idempotency, "processed");
  equal(logger.records().some((record) => record.message === "platform-smoke.job.handled"), true);

  const deliveredWorkItem = {
    ...createPlatformTestQueueMessage({
      id: "platform-smoke.work-item-accepted.work-item-1",
      type: platformSmokeWorkItemAcceptedJobMessageType,
      payload: { outboxEntryId: "platform-smoke.work-item-accepted.work-item-1" },
    }),
    idempotencyKey: "platform-smoke.work-item-accepted.work-item-1" as QueueIdempotencyKey,
  };
  equal(worker.value.enqueue(deliveredWorkItem).ok, true);
  const deliveredJob = await worker.value.runNext();
  equal(deliveredJob.ok, true);
  if (!deliveredJob.ok || deliveredJob.value.status !== "succeeded") {
    throw new Error("Expected platform-smoke durable work-item job to succeed.");
  }
  equal(logger.records().some((record) => record.message === "platform-smoke.persistence.work-item.completed"), true);

  // This is the local vertical proof: application acceptance creates the
  // immutable outbox fact; a relay converts it to a Core queue envelope; a
  // worker records durable completion and skips an identical later delivery.
  const durableOutbox = createInMemoryPlatformOutboxStore();
  const acceptedMutation = persistedMutations[0];
  if (acceptedMutation === undefined) {
    throw new Error("Expected the accepted smoke work item to stage one outbox entry.");
  }
  equal((await durableOutbox.create(acceptedMutation.outboxEntry)).ok, true);
  const relayQueue = inMemoryQueue<PlatformOutboxQueuePayload>();
  const relay = createPlatformOutboxRelay({
    outbox: durableOutbox,
    queue: relayQueue,
    owner: required(platformPersistenceLeaseOwner("platform-smoke.test.relay")),
    leaseDurationMs: 60_000,
    clock: deps.clock,
  });
  const relayed = await relay.runOnce();
  equal(relayed.ok, true);
  if (!relayed.ok || relayed.value.status !== "published") {
    throw new Error("Expected the accepted smoke outbox entry to be relayed once.");
  }
  equal(relayed.value.outboxEntryId, acceptedWorkItem.value.outboxEntryId);

  const relayedMessage = relayQueue.acceptedMessages()[0];
  if (relayedMessage === undefined) {
    throw new Error("Expected the relay to create one Core queue envelope.");
  }
  equal(relayedMessage.type, platformSmokeWorkItemAcceptedJobMessageType);
  deepEqual(relayedMessage.payload, { outboxEntryId: String(acceptedWorkItem.value.outboxEntryId) });

  const processingStore = createInMemoryPlatformProcessingStore();
  const durableWorker = await createPlatformWorkerShell({
    apps: [platformSmokeApp],
    deps,
    durableOutboxProcessing: {
      processingStore,
      owner: required(platformPersistenceLeaseOwner("platform-smoke.test.worker")),
      leaseDurationMs: 60_000,
    },
  });
  equal(durableWorker.ok, true);
  if (!durableWorker.ok) {
    throw new Error("Expected the durable platform-smoke worker to mount.");
  }
  equal((await durableWorker.value.start()).ok, true);
  const completedRecordsBefore = logger.records().filter((record) => record.message === "platform-smoke.persistence.work-item.completed").length;
  equal(durableWorker.value.enqueue(relayedMessage).ok, true);
  const firstDurableDelivery = await durableWorker.value.runNext();
  equal(firstDurableDelivery.ok, true);
  if (!firstDurableDelivery.ok || firstDurableDelivery.value.status !== "succeeded") {
    throw new Error("Expected the relayed smoke work item to complete successfully.");
  }
  equal(firstDurableDelivery.value.idempotency, "durable-processed");

  // A transport redelivery must retain the same logical identity, and must
  // therefore skip the application handler after durable completion.
  equal(durableWorker.value.enqueue(relayedMessage).ok, true);
  const duplicateDurableDelivery = await durableWorker.value.runNext();
  equal(duplicateDurableDelivery.ok, true);
  if (!duplicateDurableDelivery.ok || duplicateDurableDelivery.value.status !== "succeeded") {
    throw new Error("Expected a completed relayed smoke work item to be safely skipped.");
  }
  equal(duplicateDurableDelivery.value.idempotency, "durable-skipped");
  equal(
    logger.records().filter((record) => record.message === "platform-smoke.persistence.work-item.completed").length,
    completedRecordsBefore + 1,
  );
  const durableProcessing = await processingStore.get(acceptedWorkItem.value.outboxEntryId);
  if (durableProcessing === null) {
    throw new Error("Expected durable processing state after the relayed work item completed.");
  }
  equal(durableProcessing.state, "completed");
  equal(durableProcessing.completion?.outcome, "succeeded");
  await acceptanceDiagnosticCoverage();
}

async function acceptanceDiagnosticCoverage(): Promise<void> {
  const canary = "synthetic-private-acceptance-canary";
  const definition = defineDiagnostic({ code: "fixture.acceptance-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { lane: { type: "enum", values: ["first", "second"] }, ordinal: { type: "integer", minimum: 0, maximum: 8 } } } } as const);
  const sources = (lane: "first" | "second") => Array.from({ length: 9 }, (_, ordinal) => required(createDiagnosticRecord(definition, { lane, ordinal })));
  const first = sources("first"), second = sources("second");
  const failure = (records: readonly DiagnosticRecord[] = first) => platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED", defaultMessage: canary, params: { privateValue: canary }, diagnosticRecord: records[0]!,
    relatedDiagnosticRecords: records.slice(1), relatedDiagnosticDefinitions: [definition],
  });
  const own = persistenceLocalRejectionDiagnosticRecord({ operation: "write_atomic", field: "participant", condition: "missing", phase: "preflight", effect: "not-started" });
  const business = { schema: "core/diagnostic-record/v1", code: "platform-smoke.work-item-not-accepted", definitionVersion: 1,
    detail: { operation: "accept-work-item", reason: "operation-failed", effect: "unknown" } };
  const transaction: Transaction = { afterCommit() {} };
  const fixtureCatalog = { owner: "fixture", definitions: [definition] };
  const baseDeps = () => createPlatformTestMountDeps({ config: createPlatformTestConfigSource({ PLATFORM_SMOKE_APP_NAME: "Smoke Test" }) });
  const repository: PlatformSmokeWorkItemRepository = { async create({ workItem }) { return successful(workItem); } };
  const input = { id: required(platformSmokeWorkItemId("old-compatible-call")), acceptedAt: isoDateTimeFromDate(new Date("2026-10-30T12:00:00Z")), causationId: causationId("fixture") };
  let argumentCount = 0;
  let receivedOptions: PlatformPersistenceDiagnosticOptions | undefined;
  const compatible: PlatformPersistenceAtomicWriter = {
    async run(operation, diagnostics) {
      equal(this, compatible); argumentCount = arguments.length; receivedOptions = diagnostics;
      return operation({ transaction, async stage(mutation) { return successful(mutation); } });
    },
  };
  equal((await acceptPlatformSmokeWorkItem(input, { repository, atomicWriter: compatible })).ok, true);
  equal(argumentCount, 1);
  const explicitOptions: PlatformPersistenceDiagnosticOptions = { diagnosticDefinitions: [definition], onDiagnostic: () => undefined };
  equal((await acceptPlatformSmokeWorkItem(input, { repository, atomicWriter: compatible }, explicitOptions)).ok, true);
  equal(argumentCount, 2); equal(receivedOptions, explicitOptions);
  for (const failureAt of ["repository", "stage"] as const) {
    const rejected = err(failure());
    const calls: string[] = [];
    const rejectedRepository: PlatformSmokeWorkItemRepository = { async create({ workItem, transaction: supplied }) {
      equal(this, rejectedRepository); equal(supplied, transaction); calls.push("repository");
      return failureAt === "repository" ? rejected : successful(workItem);
    } };
    const scopedWriter: PlatformPersistenceAtomicWriter = { async run(operation, diagnostics) {
      equal(this, scopedWriter); equal(diagnostics, explicitOptions); calls.push("writer");
      return operation({ transaction, async stage() { calls.push("stage"); return rejected; } });
    } };
    equal(await acceptPlatformSmokeWorkItem(input, { repository: rejectedRepository, atomicWriter: scopedWriter }, explicitOptions), rejected);
    deepEqual(calls, failureAt === "repository" ? ["writer", "repository"] : ["writer", "repository", "stage"]);
  }

  for (const mode of ["default", "injected", "unavailable", "disabled", "metric-only"] as const) {
    let fallbackAttempts = 0;
    let observedInvocation: PlatformPersistenceDiagnosticOptions | undefined;
    const atomicWriter: PlatformPersistenceAtomicWriter = {
      async run(_operation, diagnostics) {
        observedInvocation = diagnostics;
        const selected = resolvePlatformPersistenceDiagnosticOptions({ onDiagnostic() { fallbackAttempts++; } }, diagnostics);
        observePlatformPersistenceDiagnostic(selected, own, failure());
        return err(failure());
      },
    };
    const app = createPlatformSmokeApp({ workItemAcceptance: { repository, atomicWriter }, diagnosticDefinitions: [definition] });
    const wrappedApp = { ...app, mount(registry: Parameters<typeof app.mount>[0], deps: Parameters<typeof app.mount>[1]) {
      return app.mount({ ...registry,
        registerRoute(route) { return registry.registerRoute(mode === "disabled" && route.path === "/smoke/work-items" ? { ...route, observability: { kind: "opt_out", reason: "externally_observed", justification: "Fixture disables request diagnostic reporting." } } : route); },
        registerObservabilityProfile(profile) {
          if (mode !== "metric-only" || profile.name !== platformSmokeWorkItemAcceptanceObservabilityProfileName) return registry.registerObservabilityProfile(profile);
          const { logFieldNames: _logs, traceAttributeNames: _traces, ...metricProfile } = profile;
          return registry.registerObservabilityProfile({ ...metricProfile, signals: ["metric"] });
        },
      }, deps);
    } };
    const logger = createPlatformTestLogger();
    const injected: DiagnosticRecord[] = [];
    const reporter: PlatformDiagnosticReporter = { report(record) { injected.push(record); if (mode === "unavailable") throw new Error(canary); return { status: "written" }; } };
    const deps = { ...baseDeps(), logger, ...(mode === "injected" || mode === "unavailable" ? { diagnostics: reporter } : {}) };
    const shellResult = await createPlatformServerShell({ apps: [wrappedApp], deps,
      auth: authHookForPermissions([platformSmokeWorkItemCreatePermission]), diagnosticCatalogs: [platformPersistenceDiagnosticCatalog, fixtureCatalog] });
    equal(shellResult.ok, true, `acceptance fixture ${mode} must mount`);
    const shell = required(shellResult);
    await shell.lifecycle.start();
    injected.length = 0;
    const before = logger.records().length;
    const response = await shell.handle({ method: "POST", path: "/smoke/work-items", requestId: correlationId(`acceptance-${mode}`), headers: { authorization: "Bearer write" } });
    equal(response.status, 503); deepEqual(response.body, { status: "not-accepted" });
    equal(fallbackAttempts, 0, "invocation owns the observer even when route logging is disabled");
    if (mode === "disabled" || mode === "metric-only") deepEqual(observedInvocation, {});
    const records = logger.records().slice(before).filter((record) => record.message === "platform.diagnostic.observed").map((record) => record.fields?.["diagnostic"]);
    deepEqual(records, mode === "default" ? [own, ...first, business] : []);
    deepEqual(injected, mode === "injected" || mode === "unavailable" ? [own, ...first, business] : []);
    equal(JSON.stringify(logger.records().slice(before)).includes(canary), false);
    equal(JSON.stringify(response).includes(canary), false);
    await shell.lifecycle.shutdown();
  }

  // Selection is own-data-only and explicit: neither accessors nor malformed/unselected records escape.
  let unsafeReads = 0;
  const unsafeEnvelope = {
    ...failure(),
    get diagnosticRecord(): DiagnosticRecord { unsafeReads++; throw new Error(canary); },
    relatedDiagnosticRecords: [first[0]!, { ...first[1]!, detail: { lane: canary, ordinal: 1 } }],
  };
  const unsafeWriter: PlatformPersistenceAtomicWriter = { async run(_operation, diagnostics) {
    diagnostics?.onDiagnostic?.(Object.defineProperty({ ...first[0]! }, "detail", { get() { unsafeReads++; throw new Error(canary); } }));
    return err(unsafeEnvelope);
  } };
  for (const selected of [true, false]) {
    const deps = baseDeps();
    const mounted = required(await mountPlatformAppForTest(createPlatformSmokeApp({ workItemAcceptance: { repository, atomicWriter: unsafeWriter },
      ...(selected ? { diagnosticDefinitions: [definition] } : {}) }), { deps }));
    const route = mounted.routes.find((entry) => entry.path === "/smoke/work-items"); if (!route) throw new Error("Expected route.");
    const records: DiagnosticRecord[] = [];
    const context = { ...createPlatformRuntimeRequestContext({ requestId: correlationId("safe-data"), method: "POST", path: "/smoke/work-items", logger: deps.logger, metrics: deps.metrics, clock: deps.clock, config: deps.config, flags: deps.flags }),
      onDiagnostic(record: DiagnosticRecord) { records.push(record); } };
    const response = await route.handler.handle({ params: {}, query: {}, headers: {} }, context);
    equal(response.status, 503); deepEqual(response.body, { status: "not-accepted" });
    deepEqual(records, selected ? [first[0]] : []);
    equal(JSON.stringify(records).includes(canary), false);
  }
  equal(unsafeReads, 0);

  // Exercise the real mounted handler without a Server wrapper obscuring native throws or observer attempts.
  for (const prior of ["none", "selected-only", "partial", "all", "repeated", "hostile"] as const) {
    const records: DiagnosticRecord[] = [];
    let hostileSerialization = 0;
    const envelope = prior === "repeated" ? failure(Array(9).fill(first[0])) : failure();
    const atomicWriter: PlatformPersistenceAtomicWriter = { async run(_operation, options) {
      if (prior === "selected-only") selectPlatformPersistenceDiagnosticEvidence(options ?? {}, envelope);
      if (prior === "partial") { options?.onDiagnostic?.(first[0]!); options?.onDiagnostic?.(first[1]!); }
      if (prior === "all") for (const record of first) options?.onDiagnostic?.(record);
      if (prior === "repeated") options?.onDiagnostic?.(first[0]!);
      if (prior === "hostile") options?.onDiagnostic?.({ ...first[0]!, toJSON() { hostileSerialization++; throw new Error(canary); } } as DiagnosticRecord);
      return err(envelope);
    } };
    const app = createPlatformSmokeApp({ workItemAcceptance: { repository, atomicWriter }, diagnosticDefinitions: [definition] });
    const deps = baseDeps();
    const mounted = required(await mountPlatformAppForTest(app, { deps }));
    const route = mounted.routes.find((route) => route.path === "/smoke/work-items");
    if (route === undefined) throw new Error("Expected acceptance route.");
    const context = { ...createPlatformRuntimeRequestContext({ requestId: correlationId("direct-acceptance"), method: "POST", path: "/smoke/work-items",
      logger: deps.logger, metrics: deps.metrics, clock: deps.clock, config: deps.config, flags: deps.flags }),
      onDiagnostic(record: DiagnosticRecord) { equal(this, context); records.push(record); },
    };
    const response = await route.handler.handle({ params: {}, query: {}, headers: {} }, context);
    equal(response.status, 503); deepEqual(response.body, { status: "not-accepted" });
    deepEqual(records, prior === "repeated" ? Array(9).fill(first[0]) : first, "returned fallback depends on actual attempts, preserving source multiplicity");
    deepEqual(response.observability?.diagnosticRecord, business);
    equal(hostileSerialization, 0, "untrusted toJSON must never be invoked for deduplication");
    for (const sinkMode of ["throwing", "rejecting"] as const) {
      let calls = 0;
      const failedSinkContext = { ...context, onDiagnostic() { calls++; if (sinkMode === "throwing") throw new Error(canary); return Promise.reject(new Error(canary)); } };
      const unchanged = await route.handler.handle({ params: {}, query: {}, headers: {} }, failedSinkContext);
      equal(unchanged.status, 503); equal(calls, 9);
    }
  }

  // Concurrent operations share dependencies, but never their invocation callbacks or attempt counts.
  const attemptInputs: PlatformPersistenceDiagnosticOptions[] = [];
  let releaseFirst: (() => void) | undefined;
  const secondFinished = new Promise<void>((resolve) => { releaseFirst = resolve; });
  let callOrdinal = 0;
  const concurrentWriter: PlatformPersistenceAtomicWriter = { async run(_operation, invocation) {
    const ordinal = callOrdinal++; if (invocation !== undefined) attemptInputs.push(invocation);
    if (ordinal === 0) await secondFinished;
    const envelope = failure(ordinal === 0 ? first : second);
    observePlatformPersistenceDiagnostic(invocation, own, envelope);
    if (ordinal === 1) releaseFirst!();
    return err(envelope);
  } };
  const concurrentApp = createPlatformSmokeApp({ workItemAcceptance: { repository, atomicWriter: concurrentWriter }, diagnosticDefinitions: [definition] });
  const deliveries: { record: DiagnosticRecord; context: PlatformDiagnosticContext }[] = [];
  const concurrentDeps = { ...baseDeps(), diagnostics: { report(record: DiagnosticRecord, context: PlatformDiagnosticContext) { deliveries.push({ record, context }); return { status: "written" as const }; } } };
  const shell = required(await createPlatformServerShell({ apps: [concurrentApp], deps: concurrentDeps, auth: authHookForPermissions([platformSmokeWorkItemCreatePermission]), diagnosticCatalogs: [platformPersistenceDiagnosticCatalog, fixtureCatalog] }));
  await shell.lifecycle.start(); deliveries.length = 0;
  const responses = await Promise.all(["first", "second"].map((lane) => shell.handle({ method: "POST", path: "/smoke/work-items", requestId: correlationId(`concurrent-${lane}`), headers: { authorization: "Bearer write" } })));
  deepEqual(responses.map((response) => response.status), [503, 503]);
  equal(attemptInputs.length, 2); notEqual(attemptInputs[0], attemptInputs[1]); notEqual(attemptInputs[0]?.onDiagnostic, attemptInputs[1]?.onDiagnostic);
  for (const [lane, source] of [["first", first], ["second", second]] as const) {
    deepEqual(deliveries.filter(({ context }) => context.correlationId === `concurrent-${lane}`).map(({ record }) => record), [own, ...source, business]);
  }
  await shell.lifecycle.shutdown();

  for (const code of ["PERSISTENCE_DUPLICATE", "PERSISTENCE_UNAVAILABLE"] as const) {
    const rejectedRepository: PlatformSmokeWorkItemRepository = { async create() { return err(persistenceError({ ...failure(), code })); } };
    const mounted = required(await mountPlatformAppForTest(createPlatformSmokeApp({ workItemAcceptance: { repository: rejectedRepository, atomicWriter: compatible }, diagnosticDefinitions: [definition] }), { deps: baseDeps() }));
    const route = mounted.routes.find((route) => route.path === "/smoke/work-items"); if (!route) throw new Error("Expected route.");
    const deps = baseDeps();
    const context = createPlatformRuntimeRequestContext({ requestId: correlationId("valid-id"), method: "POST", path: "/smoke/work-items", logger: deps.logger, metrics: deps.metrics, clock: deps.clock, config: deps.config, flags: deps.flags });
    const result = await route.handler.handle({ params: {}, query: {}, headers: {} }, context);
    equal(result.status, code === "PERSISTENCE_DUPLICATE" ? 409 : 503); deepEqual(result.body, { status: "not-accepted" });
  }
  const rawThrow = Object.freeze(new Error(canary));
  let writerCalls = 0;
  const throwingWriter: PlatformPersistenceAtomicWriter = { async run() { writerCalls++; throw rawThrow; } };
  const deps = baseDeps();
  const mounted = required(await mountPlatformAppForTest(createPlatformSmokeApp({ workItemAcceptance: { repository, atomicWriter: throwingWriter } }), { deps }));
  const route = mounted.routes.find((route) => route.path === "/smoke/work-items"); if (!route) throw new Error("Expected route.");
  const context = createPlatformRuntimeRequestContext({ requestId: correlationId("valid-id"), method: "POST", path: "/smoke/work-items", logger: deps.logger, metrics: deps.metrics, clock: deps.clock, config: deps.config, flags: deps.flags });
  await rejects(async () => route.handler.handle({ params: {}, query: {}, headers: {} }, context), (error: unknown) => error === rawThrow);
  equal(writerCalls, 1);
  const generatedRecords: DiagnosticRecord[] = [];
  const invalidId = await route.handler.handle({ params: {}, query: {}, headers: {} }, { ...context, requestId: correlationId(""), onDiagnostic(record) { generatedRecords.push(record); } });
  equal(invalidId.status, 500); deepEqual(invalidId.body, { status: "not-accepted" }); equal(writerCalls, 1);
  deepEqual(generatedRecords, [{ schema: "core/diagnostic-record/v1", code: "core.persistence.validation-rejected", definitionVersion: 1,
    detail: { operation: "record-id", field: "id", reason: "empty", effect: "rejected" } }]);
  await new Promise<void>((resolve) => setImmediate(resolve));
}

function createRecordingAtomicWriter(
  persistedMutations: PlatformPersistenceMutation[],
): PlatformPersistenceAtomicWriter & { readonly transaction: Transaction } {
  const transaction: Transaction = {
    afterCommit: () => undefined,
  };

  return {
    transaction,
    async run<TValue, TFailure>(operation: (
      scope: {
        readonly transaction: Transaction;
        stage(mutation: PlatformPersistenceMutation): Promise<Result<PlatformPersistenceMutation, PlatformPersistenceError>>;
      },
    ) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>): Promise<Result<TValue, TFailure | PlatformPersistenceError>> {
      return operation({
        transaction,
        async stage(mutation) {
          persistedMutations.push(mutation);
          return successful(mutation);
        },
      });
    },
  };
}

function required<TValue, TFailure>(result: Result<TValue, TFailure>): TValue {
  if (!result.ok) {
    throw new Error("Expected a valid platform-smoke test value.");
  }
  return result.value;
}

function authHookForPermissions(permissions: readonly Permission[]) {
  return {
    grantedPermissions: () => permissions,
    authenticate: (request: { readonly headers?: Readonly<Record<string, string | readonly string[]>> }) => {
      const granted = request.headers?.authorization === "Bearer read"
        ? permissions.filter((permission) => permission === platformSmokeReadPermission)
        : request.headers?.authorization === "Bearer write"
          ? permissions.filter((permission) => permission === platformSmokeWorkItemCreatePermission)
          : [];
      if (granted.length > 0) {
        return {
          authenticated: true,
          permissions: granted,
          principalId: "smoke-user",
          principalType: "user" as const,
          subject: "smoke-user",
          rateLimitKey: "principal:smoke-user",
        };
      }
      if (request.headers?.authorization === "Bearer no-permission") {
        return {
          authenticated: true,
          permissions: [],
          principalId: "smoke-limited",
          principalType: "user" as const,
          subject: "smoke-limited",
          rateLimitKey: "principal:smoke-limited",
        };
      }
      return { authenticated: false, permissions: [] };
    },
  };
}

main()
  .then(() => {
    console.log("apps/platform-smoke runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
