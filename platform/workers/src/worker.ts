import { noopTracer, type TraceSpan, type TraceSpanOutcome } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import { causationId, correlationId, type Result } from "@kanbien/core/shared";
import { tenantContext } from "@kanbien/core/tenancy";
import {
  platformProfileAllowsSignal,
  platformProfileLogFields,
  platformProfileMeasuresLatency,
  platformProfileMetricLabels,
  platformProfileTraceFields,
} from "@kanbien/platform-contracts";
import type {
  PlatformCapabilityObservabilityProfile,
  PlatformJobDeliveryDisposition,
  PlatformJobName,
  PlatformJobRegistration,
  PlatformOperationalNomenclature,
} from "@kanbien/platform-contracts";
import { assertPlatformConfigValid } from "@kanbien/platform-config";
import { platformReadiness } from "@kanbien/platform-health";
import {
  elapsedMilliseconds,
  endPlatformTraceSpan,
  platformErrorClass,
  recordPlatformMetric,
  startPlatformTraceSpan,
  writePlatformLog,
} from "@kanbien/platform-observability";
import {
  createPlatformRuntimeJobContext,
  createPlatformRuntimeLifecycle,
  mountPlatformRuntimeApps,
} from "@kanbien/platform-runtime";
import { workerError, workerFailure, type PlatformWorkerError } from "./errors";
import { createInMemoryPlatformWorkerQueue, workerQueueNow } from "./queue";
import type {
  PlatformWorkerQueueEntry,
  PlatformWorkerRunNextResult,
  PlatformWorkerShell,
  PlatformWorkerShellOptions,
} from "./types";

export async function createPlatformWorkerShell(
  options: PlatformWorkerShellOptions,
): Promise<Result<PlatformWorkerShell, PlatformWorkerError>> {
  const mounted = await mountPlatformRuntimeApps({
    apps: options.apps,
    deps: options.deps,
  });

  if (!mounted.ok) {
    return workerFailure("PLATFORM_WORKER_MOUNT_FAILED", "Platform worker failed to mount apps.", { runtimeCode: mounted.error.code }, mounted.error);
  }

  const config = assertPlatformConfigValid({
    source: options.deps.config,
    schemas: mounted.value.configSchemas,
  });
  if (!config.ok) {
    return workerFailure("PLATFORM_WORKER_CONFIG_INVALID", "Platform worker config validation failed before polling.", config.error.details, config.error);
  }

  const queue = options.queue ?? createInMemoryPlatformWorkerQueue({
    now: workerQueueNow(options.deps.clock),
  });
  const lifecycle = createPlatformRuntimeLifecycle({ apps: mounted.value.apps });
  const jobsByMessageType = new Map(mounted.value.jobs.map((job) => [String(job.messageType), job]));
  const profilesByName = new Map(mounted.value.observabilityProfiles.map((profile) => [String(profile.name), profile]));
  const tracer = options.tracer ?? noopTracer;
  const maxAttempts = options.maxAttempts ?? 3;
  const retryBackoffMs = options.retryBackoffMs ?? ((attempt: number) => attempt * 1000);

  async function runNext(): Promise<Result<PlatformWorkerRunNextResult, PlatformWorkerError>> {
    if (!lifecycle.isReady()) {
      return workerFailure("PLATFORM_WORKER_NOT_READY", "Platform worker shell is not ready.");
    }

    const entry = queue.next();
    if (entry === undefined) {
      return { ok: true, value: { status: "idle" } };
    }

    const job = jobsByMessageType.get(String(entry.message.type));
    if (job === undefined) {
      const error = workerError("PLATFORM_WORKER_JOB_NOT_FOUND", "No platform job is registered for the queue message type.", {
        messageType: String(entry.message.type),
      });
      queue.deadLetter(entry, error);
      return { ok: true, value: deadLettered(entry, error) };
    }

    const profile = workerProfileForJob(job, profilesByName);
    const startedAt = options.deps.clock.now();
    const traceSpan = startWorkerTrace(tracer, entry, profile);

    const invalidPayload = validateJobPayload(job, entry.message);
    if (invalidPayload !== undefined) {
      queue.deadLetter(entry, invalidPayload);
      recordWorkerObservation(options, entry, profile, startedAt, {
        outcome: "rejected",
        deliveryDisposition: "dead_lettered",
        error: invalidPayload,
      });
      endWorkerTrace(profile, traceSpan, {
        outcome: "rejected",
        deliveryDisposition: "dead_lettered",
        error: invalidPayload,
      });
      return { ok: true, value: deadLettered(entry, invalidPayload, job.name) };
    }

    const idempotencyKey = entry.message.idempotencyKey === undefined ? undefined : String(entry.message.idempotencyKey);
    if (idempotencyKey !== undefined && options.idempotency !== undefined) {
      try {
        if (await options.idempotency.hasProcessed(idempotencyKey)) {
          recordWorkerObservation(options, entry, profile, startedAt, {
            outcome: "succeeded",
            deliveryDisposition: "succeeded",
          });
          endWorkerTrace(profile, traceSpan, {
            outcome: "succeeded",
            deliveryDisposition: "succeeded",
          });
          return {
            ok: true,
            value: {
              status: "succeeded",
              jobName: job.name,
              message: entry.message,
              attempt: entry.attempt,
              idempotency: "skipped",
            },
          };
        }
      } catch (error) {
        const idempotencyError = workerError(
          "PLATFORM_WORKER_IDEMPOTENCY_FAILED",
          "Worker idempotency lookup failed.",
          { key: idempotencyKey },
          error,
        );
        recordWorkerObservation(options, entry, profile, startedAt, { outcome: "failed", error: idempotencyError });
        endWorkerTrace(profile, traceSpan, { outcome: "failed", error: idempotencyError });
        return { ok: false, error: idempotencyError };
      }
    }

    try {
      const context = createPlatformRuntimeJobContext({
        jobName: job.name,
        message: entry.message,
        correlationId: entry.message.correlationId ?? correlationId(String(entry.message.id)),
        causationId: causationId(String(entry.message.id)),
        ...(entry.message.tenantId === undefined ? {} : { tenant: tenantContext({ tenantId: entry.message.tenantId }) }),
        logger: options.deps.logger,
        metrics: options.deps.metrics,
        config: options.deps.config,
        flags: options.deps.flags,
        clock: options.deps.clock,
      });
      await job.handler.handle(entry.message, context);

      if (idempotencyKey !== undefined && options.idempotency !== undefined) {
        await options.idempotency.recordProcessed(idempotencyKey);
      }

      recordWorkerObservation(options, entry, profile, startedAt, {
        outcome: "succeeded",
        deliveryDisposition: "succeeded",
        handlerStarted: true,
      });
      endWorkerTrace(profile, traceSpan, {
        outcome: "succeeded",
        deliveryDisposition: "succeeded",
        handlerStarted: true,
      });
      return {
        ok: true,
        value: {
          status: "succeeded",
          jobName: job.name,
          message: entry.message,
          attempt: entry.attempt,
          idempotency: idempotencyKey === undefined ? "none" : "processed",
        },
      };
    } catch (error) {
      const workerHandlerError = workerError("PLATFORM_WORKER_HANDLER_FAILED", "Platform job handler failed.", {
        jobName: String(job.name),
        messageType: String(entry.message.type),
        attempt: entry.attempt,
      }, error);

      if (entry.attempt < maxAttempts) {
        const delayMs = retryBackoffMs(entry.attempt);
        const retry = queue.retry(entry, delayMs);
        if (!retry.ok) {
          recordWorkerObservation(options, entry, profile, startedAt, { outcome: "failed", error: retry.error, handlerStarted: true });
          endWorkerTrace(profile, traceSpan, { outcome: "failed", error: retry.error, handlerStarted: true });
          return retry;
        }

        recordWorkerObservation(options, entry, profile, startedAt, {
          outcome: "failed",
          deliveryDisposition: "retry_scheduled",
          error: workerHandlerError,
          handlerStarted: true,
        });
        endWorkerTrace(profile, traceSpan, {
          outcome: "failed",
          deliveryDisposition: "retry_scheduled",
          error: workerHandlerError,
          handlerStarted: true,
        });
        return {
          ok: true,
          value: {
            status: "retry",
            jobName: job.name,
            message: entry.message,
            attempt: entry.attempt,
            nextAttempt: entry.attempt + 1,
            delayMs,
            error: workerHandlerError,
          },
        };
      }

      queue.deadLetter(entry, workerHandlerError);
      recordWorkerObservation(options, entry, profile, startedAt, {
        outcome: "failed",
        deliveryDisposition: "dead_lettered",
        error: workerHandlerError,
        handlerStarted: true,
      });
      endWorkerTrace(profile, traceSpan, {
        outcome: "failed",
        deliveryDisposition: "dead_lettered",
        error: workerHandlerError,
        handlerStarted: true,
      });
      return { ok: true, value: deadLettered(entry, workerHandlerError, job.name) };
    }
  }

  return {
    ok: true,
    value: {
      mounted: mounted.value,
      queue,
      lifecycle,
      start: async () => {
        const started = await lifecycle.start();
        if (!started.ok) {
          return workerFailure("PLATFORM_WORKER_NOT_READY", "Platform worker lifecycle failed to start.", {}, started.error);
        }

        return workerSuccess();
      },
      enqueue: (message) => queue.enqueue(message),
      runNext,
      runUntilIdle: async (runOptions = {}) => {
        const maxIterations = runOptions.maxIterations ?? 100;
        const results: PlatformWorkerRunNextResult[] = [];

        for (let index = 0; index < maxIterations; index += 1) {
          const result = await runNext();
          if (!result.ok) {
            return result;
          }

          results.push(result.value);
          if (result.value.status === "idle") {
            break;
          }
        }

        return { ok: true, value: results };
      },
      health: () => platformReadiness({
        lifecycleReady: lifecycle.isReady(),
        healthChecks: mounted.value.healthChecks,
        clock: options.deps.clock,
      }),
      shutdown: async () => {
        queue.close();
        const shutdown = await lifecycle.shutdown();
        if (!shutdown.ok) {
          return workerFailure("PLATFORM_WORKER_NOT_READY", "Platform worker lifecycle failed to shut down.", {}, shutdown.error);
        }

        return workerSuccess();
      },
    },
  };
}

function validateJobPayload(job: PlatformJobRegistration, message: QueueMessage): PlatformWorkerError | undefined {
  if (job.validator === undefined || job.validator.validate(message.payload)) {
    return undefined;
  }

  return workerError("PLATFORM_WORKER_INVALID_PAYLOAD", "Queue message payload failed job validation.", {
    jobName: String(job.name),
    messageType: String(message.type),
  });
}

function deadLettered(
  entry: PlatformWorkerQueueEntry,
  error: PlatformWorkerError,
  jobName?: PlatformJobName,
): PlatformWorkerRunNextResult {
  return {
    status: "dead-lettered",
    message: entry.message,
    attempt: entry.attempt,
    error,
    ...(jobName === undefined ? {} : { jobName }),
  };
}

function workerProfileForJob(
  job: PlatformJobRegistration,
  profilesByName: ReadonlyMap<string, PlatformCapabilityObservabilityProfile>,
): PlatformCapabilityObservabilityProfile | undefined {
  if (job.observability.kind !== "profile") {
    return undefined;
  }

  return profilesByName.get(String(job.observability.profile));
}

function recordWorkerObservation(
  options: PlatformWorkerShellOptions,
  entry: PlatformWorkerQueueEntry,
  profile: PlatformCapabilityObservabilityProfile | undefined,
  startedAt: Date,
  event: PlatformWorkerObservabilityEvent,
): void {
  if (profile === undefined) {
    return;
  }

  const nomenclature = workerNomenclature(profile, event);
  if (platformProfileAllowsSignal(profile, "operational_log")) {
    writePlatformLog(options.deps.logger, {
      level: workerLogLevel(event),
      message: "platform.worker.job.delivery",
      fields: platformProfileLogFields(profile, nomenclature),
    });
  }

  if (!platformProfileAllowsSignal(profile, "metric")) {
    return;
  }

  const labels = platformProfileMetricLabels(profile, nomenclature);
  recordPlatformMetric(options.deps.metrics, options.deps.clock, {
    name: "platform.worker.job.delivery",
    labels,
  });

  const finishedAt = options.deps.clock.now();
  if (event.handlerStarted && platformProfileMeasuresLatency(profile, "job_execution_latency")) {
    recordPlatformMetric(options.deps.metrics, options.deps.clock, {
      name: "platform.worker.job.execution_latency",
      kind: "timer",
      value: elapsedMilliseconds(startedAt, finishedAt),
      unit: "ms",
      labels,
    });
  }

  if (platformProfileMeasuresLatency(profile, "queue_wait_latency")) {
    recordPlatformMetric(options.deps.metrics, options.deps.clock, {
      name: "platform.worker.job.queue_wait_latency",
      kind: "timer",
      value: elapsedMilliseconds(new Date(entry.enqueuedAt), startedAt),
      unit: "ms",
      labels,
    });
  }
}

function endWorkerTrace(
  profile: PlatformCapabilityObservabilityProfile | undefined,
  span: TraceSpan | undefined,
  event: PlatformWorkerObservabilityEvent,
): void {
  if (profile === undefined || span === undefined) {
    return;
  }

  endPlatformTraceSpan(span, {
    outcome: event.outcome,
    attributes: platformProfileTraceFields(profile, workerNomenclature(profile, event)),
  });
}

function startWorkerTrace(
  tracer: PlatformWorkerShellOptions["tracer"] | undefined,
  entry: PlatformWorkerQueueEntry,
  profile: PlatformCapabilityObservabilityProfile | undefined,
): TraceSpan | undefined {
  if (profile === undefined || !platformProfileAllowsSignal(profile, "trace")) {
    return undefined;
  }

  return startPlatformTraceSpan(tracer ?? noopTracer, {
    name: "platform.worker.job",
    ...(entry.message.traceParent === undefined ? {} : { parent: entry.message.traceParent }),
  });
}

function workerNomenclature(
  profile: PlatformCapabilityObservabilityProfile,
  event: PlatformWorkerObservabilityEvent,
): PlatformOperationalNomenclature {
  return {
    capability: profile.capability,
    action: profile.action,
    executionContext: "worker",
    outcome: event.outcome,
    ...(event.deliveryDisposition === undefined ? {} : { jobDeliveryDisposition: event.deliveryDisposition }),
    ...(event.error === undefined ? {} : { errorClass: platformErrorClass(event.error) }),
  };
}

function workerLogLevel(event: PlatformWorkerObservabilityEvent): "info" | "warn" | "error" {
  if (event.outcome === "succeeded") {
    return "info";
  }

  if (event.outcome === "rejected" || event.deliveryDisposition === "retry_scheduled") {
    return "warn";
  }

  return "error";
}

interface PlatformWorkerObservabilityEvent {
  readonly outcome: TraceSpanOutcome;
  readonly deliveryDisposition?: PlatformJobDeliveryDisposition;
  readonly error?: PlatformWorkerError;
  readonly handlerStarted?: boolean;
}

function workerSuccess(): Result<void, PlatformWorkerError> {
  return { ok: true, value: undefined };
}
