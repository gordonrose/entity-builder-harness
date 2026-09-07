import { noopTracer, type TraceSpan, type TraceSpanOutcome } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import { causationId, correlationId, type JsonValue, type Result } from "@kanbien/core/shared";
import { tenantContext } from "@kanbien/core/tenancy";
import type { PlatformJobName, PlatformJobRegistration } from "@kanbien/platform-contracts";
import { assertPlatformConfigValid } from "@kanbien/platform-config";
import { platformReadiness } from "@kanbien/platform-health";
import {
  elapsedMilliseconds,
  endPlatformTraceSpan,
  platformErrorClass,
  recordPlatformJobMetric,
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
  PlatformWorkerRunStatus,
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

    const startedAt = options.deps.clock.now();
    const traceSpan = startPlatformTraceSpan(tracer, {
      name: "platform.worker.job",
      ...(entry.message.traceParent === undefined ? {} : { parent: entry.message.traceParent }),
      attributes: {
        job: String(entry.message.type),
        retryCount: entry.attempt - 1,
      },
    });

    const job = jobsByMessageType.get(String(entry.message.type));
    if (job === undefined) {
      const error = workerError("PLATFORM_WORKER_JOB_NOT_FOUND", "No platform job is registered for the queue message type.", {
        messageType: String(entry.message.type),
      });
      queue.deadLetter(entry, error);
      recordWorkerAttempt(options, entry, "dead-lettered", undefined, error);
      writeWorkerLog(options, "warn", "platform.worker.job.dead_lettered", entry, undefined, error);
      endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "rejected", error });
      return { ok: true, value: deadLettered(entry, error) };
    }

    const invalidPayload = validateJobPayload(job, entry.message);
    if (invalidPayload !== undefined) {
      queue.deadLetter(entry, invalidPayload);
      recordWorkerAttempt(options, entry, "dead-lettered", job.name, invalidPayload);
      writeWorkerLog(options, "warn", "platform.worker.job.dead_lettered", entry, job.name, invalidPayload);
      endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "rejected", jobName: job.name, error: invalidPayload });
      return { ok: true, value: deadLettered(entry, invalidPayload, job.name) };
    }

    const idempotencyKey = entry.message.idempotencyKey === undefined ? undefined : String(entry.message.idempotencyKey);
    if (idempotencyKey !== undefined && options.idempotency !== undefined) {
      try {
        if (await options.idempotency.hasProcessed(idempotencyKey)) {
          recordWorkerAttempt(options, entry, "succeeded", job.name);
          writeWorkerLog(options, "info", "platform.worker.job.skipped", entry, job.name);
          endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "succeeded", jobName: job.name });
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
        endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "failed", jobName: job.name, error: idempotencyError });
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

      writePlatformLog(options.deps.logger, {
        level: "info",
        message: "platform.worker.job.succeeded",
        fields: workerLogFields(entry, job.name),
      });
      recordWorkerAttempt(options, entry, "succeeded", job.name);
      endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "succeeded", jobName: job.name });
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
          endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "failed", jobName: job.name, error: retry.error });
          return retry;
        }

        writePlatformLog(options.deps.logger, {
          level: "warn",
          message: "platform.worker.job.retry",
          fields: {
            ...workerLogFields(entry, job.name),
            nextAttempt: entry.attempt + 1,
            delayMs,
          },
          error: workerHandlerError,
        });
        recordWorkerAttempt(options, entry, "retry", job.name, workerHandlerError);
        endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "failed", jobName: job.name, error: workerHandlerError });
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
      writePlatformLog(options.deps.logger, {
        level: "error",
        message: "platform.worker.job.dead_lettered",
        fields: workerLogFields(entry, job.name),
        error: workerHandlerError,
      });
      recordWorkerAttempt(options, entry, "dead-lettered", job.name, workerHandlerError);
      endWorkerTrace(options, entry, traceSpan, startedAt, { outcome: "failed", jobName: job.name, error: workerHandlerError });
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

function recordWorkerAttempt(
  options: PlatformWorkerShellOptions,
  entry: PlatformWorkerQueueEntry,
  status: Exclude<PlatformWorkerRunStatus, "idle">,
  jobName?: PlatformJobName,
  error?: PlatformWorkerError,
): void {
  recordPlatformJobMetric(options.deps.metrics, options.deps.clock, {
    job: jobName === undefined ? String(entry.message.type) : String(jobName),
    status,
    retryCount: entry.attempt - 1,
    ...(error === undefined ? {} : { errorClass: error.code }),
  });
}

function endWorkerTrace(
  options: PlatformWorkerShellOptions,
  entry: PlatformWorkerQueueEntry,
  span: TraceSpan,
  startedAt: Date,
  input: {
    readonly outcome: TraceSpanOutcome;
    readonly jobName?: PlatformJobName;
    readonly error?: unknown;
  },
): void {
  endPlatformTraceSpan(span, {
    outcome: input.outcome,
    attributes: {
      job: input.jobName === undefined ? String(entry.message.type) : String(input.jobName),
      retryCount: entry.attempt - 1,
      latencyMs: elapsedMilliseconds(startedAt, options.deps.clock.now()),
      outcome: input.outcome,
      ...(input.error === undefined ? {} : { errorClass: platformErrorClass(input.error) }),
    },
  });
}

function writeWorkerLog(
  options: PlatformWorkerShellOptions,
  level: "info" | "warn" | "error",
  message: string,
  entry: PlatformWorkerQueueEntry,
  jobName?: PlatformJobName,
  error?: PlatformWorkerError,
): void {
  writePlatformLog(options.deps.logger, {
    level,
    message,
    fields: workerLogFields(entry, jobName),
    ...(error === undefined ? {} : { error }),
  });
}

function workerLogFields(
  entry: PlatformWorkerQueueEntry,
  jobName?: PlatformJobName,
): Readonly<Record<string, JsonValue>> {
  return {
    jobName: jobName === undefined ? String(entry.message.type) : String(jobName),
    messageType: String(entry.message.type),
    attempt: entry.attempt,
  };
}

function workerSuccess(): Result<void, PlatformWorkerError> {
  return { ok: true, value: undefined };
}
