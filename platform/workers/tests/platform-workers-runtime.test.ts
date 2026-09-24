import { deepEqual, equal } from "node:assert/strict";
import { configError, type ConfigSchema } from "@kanbien/core/config";
import type { Logger } from "@kanbien/core/logging";
import { createInMemoryTracer, spanId, traceContext, traceId, type Metrics, type Tracer } from "@kanbien/core/monitoring";
import { outboxEntryId } from "@kanbien/core/persistence";
import type { QueueIdempotencyKey, QueueMessageType } from "@kanbien/core/queues";
import { causationId } from "@kanbien/core/shared";
import { tenantId, type TenantContext } from "@kanbien/core/tenancy";
import { validationIssue } from "@kanbien/core/validation";
import {
  definePlatformApp,
  platformAppId,
  platformCapabilityName,
  platformJobName,
  platformObservabilityProfileName,
} from "@kanbien/platform-contracts";
import {
  createPlatformTestLogger,
  createPlatformTestMetrics,
  createPlatformTestMountDeps,
  createPlatformTestQueueMessage,
  validatorForTest,
} from "@kanbien/platform-testing";
import {
  createInMemoryPlatformWorkerIdempotencyStore,
  createPlatformWorkerShell,
} from "../src/index";
import {
  createInMemoryPlatformProcessingStore,
  platformPersistenceLeaseOwner,
  type PlatformPersistenceObservation,
} from "@kanbien/platform-persistence";

async function main(): Promise<void> {
  const appId = platformAppId("smoke");
  const jobName = platformJobName("smoke.rebuild");
  const failingJobName = platformJobName("smoke.failing");
  const profileName = platformObservabilityProfileName("smoke.worker.execute");
  const capabilityName = platformCapabilityName("smoke.worker.execute");
  if (!appId.ok || !jobName.ok || !failingJobName.ok || !profileName.ok || !capabilityName.ok) {
    throw new Error("Expected valid worker test primitives.");
  }

  let handled = 0;
  let handledTenant: TenantContext | undefined;
  let handledCausation: string | undefined;
  let handlerReceivedTraceParent = false;
  let failingAttempts = 0;
  let tenantlessJobTenant: TenantContext | undefined;
  const logger = createPlatformTestLogger();
  const metrics = createPlatformTestMetrics();
  const deps = createPlatformTestMountDeps({ logger, metrics });
  const testObservability = { kind: "profile", profile: profileName.value } as const;
  const testProfile = {
    name: profileName.value,
    capability: capabilityName.value,
    action: "execute" as const,
    signals: ["operational_log", "metric", "trace"] as const,
    logFieldNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"] as const,
    metricDimensionFieldNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"] as const,
    traceAttributeNames: ["capability", "action", "execution_context", "job_delivery_disposition", "outcome", "error_class"] as const,
    nfrObjectives: [{ nfrClass: "async_completion" as const, measurement: "job_execution_latency" as const }],
  };
  const app = definePlatformApp({
    id: appId.value,
    name: "Smoke",
    mount(registry) {
      registry.registerObservabilityProfile(testProfile);
      registry.registerJob({
        name: jobName.value,
        messageType: "smoke.rebuild" as QueueMessageType,
        observability: testObservability,
        validator: validatorForTest((value): value is { readonly rebuild: boolean } =>
          typeof value === "object"
          && value !== null
          && "rebuild" in value
          && typeof (value as { readonly rebuild?: unknown }).rebuild === "boolean"),
        handler: {
          handle: (_message, context) => {
            handled += 1;
            handledTenant = context.tenant;
            handledCausation = context.causationId;
            handlerReceivedTraceParent = "traceParent" in context;
          },
        },
      });
      registry.registerJob({
        name: failingJobName.value,
        messageType: "smoke.failing" as QueueMessageType,
        observability: testObservability,
        handler: {
          handle: (_message, context) => {
            failingAttempts += 1;
            tenantlessJobTenant = context.tenant;
            throw new Error("fail");
          },
        },
      });
    },
  });

  const idempotency = createInMemoryPlatformWorkerIdempotencyStore();
  const tracer = createInMemoryTracer();
  const shell = await createPlatformWorkerShell({ apps: [app], deps, idempotency, tracer, maxAttempts: 2, retryBackoffMs: () => 25 });
  equal(shell.ok, true);
  if (!shell.ok) {
    throw new Error("Expected worker shell to mount.");
  }

  const beforeStart = await shell.value.runNext();
  equal(beforeStart.ok, false);
  if (beforeStart.ok) {
    throw new Error("Expected run before start to fail.");
  }
  equal(beforeStart.error.code, "PLATFORM_WORKER_NOT_READY");

  equal((await shell.value.start()).ok, true);
  const ready = await shell.value.health();
  equal(ready.status, "ready");

  const successMessage = {
    ...createPlatformTestQueueMessage({
      id: "success-1",
      type: "smoke.rebuild" as QueueMessageType,
      payload: { rebuild: true },
    }),
    idempotencyKey: "idem-1" as QueueIdempotencyKey,
    tenantId: tenantId("tenant-123"),
    causationId: causationId("event-17"),
    traceParent: traceContext({
      traceId: traceId("trace-17"),
      spanId: spanId("span-17"),
    }),
  };
  equal(shell.value.enqueue(successMessage).ok, true);
  const success = await shell.value.runNext();
  equal(success.ok, true);
  if (!success.ok) {
    throw new Error("Expected worker success.");
  }
  equal(success.value.status, "succeeded");
  if (success.value.status !== "succeeded") {
    throw new Error("Expected succeeded status.");
  }
  equal(success.value.idempotency, "processed");
  equal(handled, 1);
  equal(handledTenant?.tenantId, "tenant-123");
  equal(handledCausation, "success-1");
  equal(successMessage.causationId, "event-17");
  equal(handlerReceivedTraceParent, false);
  deepEqual(tracer.spans()[0], {
    name: "platform.worker.job",
    context: {
      traceId: "trace-17",
      spanId: "span-1",
      parentSpanId: "span-17",
    },
    end: {
      outcome: "succeeded",
      attributes: {
        capability: "smoke.worker.execute",
        action: "execute",
        execution_context: "worker",
        job_delivery_disposition: "succeeded",
        outcome: "succeeded",
      },
    },
  });

  equal(shell.value.enqueue(successMessage).ok, true);
  const skipped = await shell.value.runNext();
  equal(skipped.ok, true);
  if (!skipped.ok || skipped.value.status !== "succeeded") {
    throw new Error("Expected idempotency skip to succeed.");
  }
  equal(skipped.value.idempotency, "skipped");
  equal(handled, 1);

  equal(shell.value.enqueue(createPlatformTestQueueMessage({
    id: "invalid-1",
    type: "smoke.rebuild" as QueueMessageType,
    payload: { rebuild: "nope" },
  })).ok, true);
  const invalid = await shell.value.runNext();
  equal(invalid.ok, true);
  if (!invalid.ok || invalid.value.status !== "dead-lettered") {
    throw new Error("Expected invalid payload to dead-letter.");
  }
  equal(invalid.value.error.code, "PLATFORM_WORKER_INVALID_PAYLOAD");

  equal(shell.value.enqueue(createPlatformTestQueueMessage({
    id: "failing-1",
    type: "smoke.failing" as QueueMessageType,
    payload: { ok: true },
  })).ok, true);
  const retry = await shell.value.runNext();
  equal(retry.ok, true);
  if (!retry.ok || retry.value.status !== "retry") {
    throw new Error("Expected failing job to retry.");
  }
  equal(retry.value.nextAttempt, 2);
  equal(retry.value.delayMs, 25);

  const deadLetter = await shell.value.runNext();
  equal(deadLetter.ok, true);
  if (!deadLetter.ok || deadLetter.value.status !== "dead-lettered") {
    throw new Error("Expected failing job to dead-letter after retry.");
  }
  equal(deadLetter.value.error.code, "PLATFORM_WORKER_HANDLER_FAILED");
  equal(failingAttempts, 2);
  equal(tenantlessJobTenant, undefined);
  equal(shell.value.queue.deadLetters().length, 2);
  equal(metrics.points().length, 8);
  equal(metrics.points().filter((point) => point.name === "platform.worker.job.delivery").length, 5);
  equal(metrics.points().filter((point) => point.name === "platform.worker.job.execution_latency").length, 3);
  deepEqual(metrics.points()[0]?.labels, {
    capability: "smoke.worker.execute",
    action: "execute",
    execution_context: "worker",
    job_delivery_disposition: "succeeded",
    outcome: "succeeded",
  });
  equal(metrics.points().some((point) => "job" in (point.labels ?? {})), false);
  equal(metrics.points().some((point) => "retry_count" in (point.labels ?? {})), false);
  equal(logger.records().filter((record) => record.message === "platform.worker.job.delivery").length, 5);
  deepEqual(logger.records()[0]?.fields, {
    capability: "smoke.worker.execute",
    action: "execute",
    execution_context: "worker",
    job_delivery_disposition: "succeeded",
    outcome: "succeeded",
  });
  equal(logger.records().some((record) => "messageType" in (record.fields ?? {})), false);

  const idle = await shell.value.runUntilIdle();
  equal(idle.ok, true);
  if (!idle.ok) {
    throw new Error("Expected runUntilIdle to pass.");
  }
  equal(idle.value.at(-1)?.status, "idle");

  equal((await shell.value.shutdown()).ok, true);
  const notReady = await shell.value.health();
  equal(notReady.status, "not-ready");
  equal(shell.value.enqueue(createPlatformTestQueueMessage({
    id: "closed-1",
    type: "smoke.rebuild" as QueueMessageType,
    payload: { rebuild: true },
  })).ok, false);

  const invalidConfigSchema: ConfigSchema<never> = {
    parse: () => ({
      ok: false,
      error: configError("CONFIG_INVALID", [
        validationIssue({
          path: ["config", "SMOKE_SECRET"],
          code: "CONFIG_INVALID_SECRET",
          defaultMessage: "Smoke config is invalid.",
          params: { secret: "do-not-leak" },
        }),
      ]),
    }),
  };
  const invalidConfigShell = await createPlatformWorkerShell({
    apps: [definePlatformApp({
      id: appId.value,
      name: "Invalid Config",
      mount(registry) {
        registry.registerConfigSchema(invalidConfigSchema);
      },
    })],
    deps: createPlatformTestMountDeps(),
  });
  equal(invalidConfigShell.ok, false);
  if (!invalidConfigShell.ok) {
    equal(invalidConfigShell.error.code, "PLATFORM_WORKER_CONFIG_INVALID");
    equal(JSON.stringify(invalidConfigShell.error.details).includes("do-not-leak"), false);
  }

  const optOutJobName = platformJobName("smoke.opt-out");
  if (!optOutJobName.ok) {
    throw new Error("Expected opt-out job name to be valid.");
  }
  const optOutLogger = createPlatformTestLogger();
  const optOutMetrics = createPlatformTestMetrics();
  const optOutShell = await createPlatformWorkerShell({
    apps: [definePlatformApp({
      id: appId.value,
      name: "Opt out",
      mount(registry) {
        registry.registerJob({
          name: optOutJobName.value,
          messageType: "smoke.opt-out" as QueueMessageType,
          observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture proves profile opt-out behavior." },
          handler: { handle: () => undefined },
        });
      },
    })],
    deps: createPlatformTestMountDeps({ logger: optOutLogger, metrics: optOutMetrics }),
    tracer: createInMemoryTracer(),
  });
  equal(optOutShell.ok, true);
  if (!optOutShell.ok) {
    throw new Error("Expected opt-out worker shell to mount.");
  }
  equal((await optOutShell.value.start()).ok, true);
  equal(optOutShell.value.enqueue(createPlatformTestQueueMessage({
    id: "opt-out-1",
    type: "smoke.opt-out" as QueueMessageType,
    payload: {},
  })).ok, true);
  equal((await optOutShell.value.runNext()).ok, true);
  equal(optOutLogger.records().length, 0);
  equal(optOutMetrics.points().length, 0);

  const resilientJobName = platformJobName("smoke.resilient");
  if (!resilientJobName.ok) {
    throw new Error("Expected resilient job name to be valid.");
  }
  let resilientHandled = 0;
  const unavailableLogger: Logger = { write: () => { throw new Error("logger unavailable"); } };
  const unavailableMetrics: Metrics = { record: () => { throw new Error("metrics unavailable"); } };
  const unavailableTracer: Tracer = { startSpan: () => { throw new Error("tracer unavailable"); } };
  const resilientShell = await createPlatformWorkerShell({
    apps: [definePlatformApp({
      id: appId.value,
      name: "Resilient",
      mount(registry) {
        registry.registerObservabilityProfile(testProfile);
        registry.registerJob({
          name: resilientJobName.value,
          messageType: "smoke.resilient" as QueueMessageType,
          observability: testObservability,
          handler: { handle: () => { resilientHandled += 1; } },
        });
      },
    })],
    deps: createPlatformTestMountDeps({ logger: unavailableLogger, metrics: unavailableMetrics }),
    tracer: unavailableTracer,
  });
  equal(resilientShell.ok, true);
  if (!resilientShell.ok) {
    throw new Error("Expected resilient worker shell to mount.");
  }
  equal((await resilientShell.value.start()).ok, true);
  equal(resilientShell.value.enqueue(createPlatformTestQueueMessage({
    id: "resilient-1",
    type: "smoke.resilient" as QueueMessageType,
    payload: {},
  })).ok, true);
  const resilientResult = await resilientShell.value.runNext();
  equal(resilientResult.ok, true);
  if (!resilientResult.ok) {
    throw new Error("Expected unavailable telemetry to leave the job result unchanged.");
  }
  equal(resilientResult.value.status, "succeeded");
  equal(resilientHandled, 1);

  const durableJobName = platformJobName("smoke.durable");
  const flakyDurableJobName = platformJobName("smoke.durable-flaky");
  const terminalDurableJobName = platformJobName("smoke.durable-terminal");
  const durableOwner = platformPersistenceLeaseOwner("worker.durable-a");
  if (!durableJobName.ok || !flakyDurableJobName.ok || !terminalDurableJobName.ok || !durableOwner.ok) {
    throw new Error("Expected valid durable worker test primitives.");
  }

  let durableHandled = 0;
  let flakyDurableHandled = 0;
  let terminalDurableHandled = 0;
  const durableProcessingStore = createInMemoryPlatformProcessingStore();
  const durableObservations: PlatformPersistenceObservation[] = [];
  const durableApp = definePlatformApp({
    id: appId.value,
    name: "Durable outbox worker",
    mount(registry) {
      registry.registerJob({
        name: durableJobName.value,
        messageType: "smoke.durable" as QueueMessageType,
        observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture proves durable-outbox worker processing." },
        validator: validatorForTest((value): value is { readonly outboxEntryId: string } =>
          typeof value === "object"
          && value !== null
          && "outboxEntryId" in value
          && typeof (value as { readonly outboxEntryId?: unknown }).outboxEntryId === "string"),
        handler: { handle: () => { durableHandled += 1; } },
      });
      registry.registerJob({
        name: flakyDurableJobName.value,
        messageType: "smoke.durable-flaky" as QueueMessageType,
        observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture proves durable processing release before worker retry." },
        validator: validatorForTest((value): value is { readonly outboxEntryId: string } =>
          typeof value === "object"
          && value !== null
          && "outboxEntryId" in value
          && typeof (value as { readonly outboxEntryId?: unknown }).outboxEntryId === "string"),
        handler: {
          handle: () => {
            flakyDurableHandled += 1;
            if (flakyDurableHandled === 1) throw new Error("First durable attempt fails.");
          },
        },
      });
      registry.registerJob({
        name: terminalDurableJobName.value,
        messageType: "smoke.durable-terminal" as QueueMessageType,
        observability: { kind: "opt_out", reason: "non_user_workload_path", justification: "Fixture proves terminal durable failure before dead-lettering." },
        validator: validatorForTest((value): value is { readonly outboxEntryId: string } =>
          typeof value === "object"
          && value !== null
          && "outboxEntryId" in value
          && typeof (value as { readonly outboxEntryId?: unknown }).outboxEntryId === "string"),
        handler: { handle: () => { terminalDurableHandled += 1; throw new Error("Terminal durable failure."); } },
      });
    },
  });
  const durableShell = await createPlatformWorkerShell({
    apps: [durableApp],
    deps: createPlatformTestMountDeps(),
    durableOutboxProcessing: {
      processingStore: durableProcessingStore,
      owner: durableOwner.value,
      leaseDurationMs: 1_000,
      observer: { record: (observation) => durableObservations.push(observation) },
    },
    maxAttempts: 2,
    retryBackoffMs: () => 0,
  });
  equal(durableShell.ok, true);
  if (!durableShell.ok) {
    throw new Error("Expected durable worker shell to mount.");
  }
  equal((await durableShell.value.start()).ok, true);

  const durableMessage = {
    ...createPlatformTestQueueMessage({
      id: "outbox-worker-1",
      type: "smoke.durable" as QueueMessageType,
      payload: { outboxEntryId: "outbox-worker-1" },
    }),
    idempotencyKey: "outbox-worker-1" as QueueIdempotencyKey,
  };
  equal(durableShell.value.enqueue(durableMessage).ok, true);
  const durableSuccess = await durableShell.value.runNext();
  equal(durableSuccess.ok, true);
  if (!durableSuccess.ok || durableSuccess.value.status !== "succeeded") {
    throw new Error("Expected a durable outbox delivery to succeed.");
  }
  equal(durableSuccess.value.idempotency, "durable-processed");
  equal(durableHandled, 1);
  const durableCompleted = await durableProcessingStore.get(outboxEntryId("outbox-worker-1"));
  equal(durableCompleted?.state, "completed");
  equal(durableCompleted?.completion?.outcome, "succeeded");

  equal(durableShell.value.enqueue(durableMessage).ok, true);
  const durableDuplicate = await durableShell.value.runNext();
  equal(durableDuplicate.ok, true);
  if (!durableDuplicate.ok || durableDuplicate.value.status !== "succeeded") {
    throw new Error("Expected an already-completed durable delivery to be acknowledged safely.");
  }
  equal(durableDuplicate.value.idempotency, "durable-skipped");
  equal(durableHandled, 1);

  const flakyMessage = {
    ...createPlatformTestQueueMessage({
      id: "outbox-worker-2",
      type: "smoke.durable-flaky" as QueueMessageType,
      payload: { outboxEntryId: "outbox-worker-2" },
    }),
    idempotencyKey: "outbox-worker-2" as QueueIdempotencyKey,
  };
  equal(durableShell.value.enqueue(flakyMessage).ok, true);
  const durableRetry = await durableShell.value.runNext();
  equal(durableRetry.ok, true);
  if (!durableRetry.ok || durableRetry.value.status !== "retry") {
    throw new Error("Expected a failed durable handler to release its claim before retry.");
  }
  const releasedDurable = await durableProcessingStore.get(outboxEntryId("outbox-worker-2"));
  equal(releasedDurable?.state, "retry-eligible");
  equal(releasedDurable?.attempt, 1);
  const flakySuccess = await durableShell.value.runNext();
  equal(flakySuccess.ok, true);
  if (!flakySuccess.ok || flakySuccess.value.status !== "succeeded") {
    throw new Error("Expected the released durable processing claim to be reclaimable for retry.");
  }
  equal(flakySuccess.value.idempotency, "durable-processed");
  equal(flakyDurableHandled, 2);
  const flakyCompleted = await durableProcessingStore.get(outboxEntryId("outbox-worker-2"));
  equal(flakyCompleted?.state, "completed");
  equal(flakyCompleted?.attempt, 2);

  const invalidDurableEnvelope = {
    ...createPlatformTestQueueMessage({
      id: "transport-generated-id",
      type: "smoke.durable" as QueueMessageType,
      payload: { outboxEntryId: "outbox-worker-invalid" },
    }),
    idempotencyKey: "outbox-worker-invalid" as QueueIdempotencyKey,
  };
  equal(durableShell.value.enqueue(invalidDurableEnvelope).ok, true);
  const rejectedDurableEnvelope = await durableShell.value.runNext();
  equal(rejectedDurableEnvelope.ok, true);
  if (!rejectedDurableEnvelope.ok || rejectedDurableEnvelope.value.status !== "dead-lettered") {
    throw new Error("Expected an unstable durable outbox envelope to be rejected.");
  }
  equal(rejectedDurableEnvelope.value.error.code, "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID");
  deepEqual(durableObservations.map((observation) => ({
    transition: observation.transition,
    outcome: observation.outcome,
    fields: Object.keys(observation).sort(),
  })), [
    { transition: "processing.claimed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.completed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.duplicate_succeeded", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.claimed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.retry_released", outcome: "failed", fields: ["error", "outcome", "transition"] },
    { transition: "processing.claimed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.completed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.envelope_rejected", outcome: "rejected", fields: ["error", "outcome", "transition"] },
  ]);

  const terminalProcessingStore = createInMemoryPlatformProcessingStore();
  const terminalDurableObservations: PlatformPersistenceObservation[] = [];
  const terminalDurableShell = await createPlatformWorkerShell({
    apps: [durableApp],
    deps: createPlatformTestMountDeps(),
    durableOutboxProcessing: {
      processingStore: terminalProcessingStore,
      owner: durableOwner.value,
      leaseDurationMs: 1_000,
      observer: { record: (observation) => terminalDurableObservations.push(observation) },
    },
    maxAttempts: 1,
  });
  equal(terminalDurableShell.ok, true);
  if (!terminalDurableShell.ok) {
    throw new Error("Expected terminal durable worker shell to mount.");
  }
  equal((await terminalDurableShell.value.start()).ok, true);
  const terminalMessage = {
    ...createPlatformTestQueueMessage({
      id: "outbox-worker-3",
      type: "smoke.durable-terminal" as QueueMessageType,
      payload: { outboxEntryId: "outbox-worker-3" },
    }),
    idempotencyKey: "outbox-worker-3" as QueueIdempotencyKey,
  };
  equal(terminalDurableShell.value.enqueue(terminalMessage).ok, true);
  const terminalResult = await terminalDurableShell.value.runNext();
  equal(terminalResult.ok, true);
  if (!terminalResult.ok || terminalResult.value.status !== "dead-lettered") {
    throw new Error("Expected terminal worker failure to finish durable processing before dead-lettering.");
  }
  equal(terminalDurableHandled, 1);
  const terminalCompleted = await terminalProcessingStore.get(outboxEntryId("outbox-worker-3"));
  equal(terminalCompleted?.state, "completed");
  equal(terminalCompleted?.completion?.outcome, "terminal-failure");
  equal(terminalDurableShell.value.enqueue(terminalMessage).ok, true);
  const terminalDuplicate = await terminalDurableShell.value.runNext();
  equal(terminalDuplicate.ok, true);
  if (!terminalDuplicate.ok || terminalDuplicate.value.status !== "dead-lettered") {
    throw new Error("Expected a terminal durable duplicate to preserve the dead-letter outcome.");
  }
  equal(terminalDuplicate.value.error.code, "PLATFORM_WORKER_DURABLE_PROCESSING_TERMINAL_FAILURE");
  equal(terminalDurableHandled, 1);
  deepEqual(terminalDurableObservations.map((observation) => ({
    transition: observation.transition,
    outcome: observation.outcome,
    fields: Object.keys(observation).sort(),
  })), [
    { transition: "processing.claimed", outcome: "succeeded", fields: ["outcome", "transition"] },
    { transition: "processing.terminal_failure_recorded", outcome: "failed", fields: ["error", "outcome", "transition"] },
    { transition: "processing.duplicate_terminal_failure", outcome: "failed", fields: ["error", "outcome", "transition"] },
  ]);
}

main()
  .then(() => {
    console.log("platform/workers runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
