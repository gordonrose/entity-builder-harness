import { deepEqual, equal } from "node:assert/strict";
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
} from "@kanbien/platform-persistence";
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
