import { metricName, metricUnit } from "@kanbien/core/monitoring";
import type { QueueMessage } from "@kanbien/core/queues";
import {
  correlationId,
  isoDateTimeFromDate,
  type CorrelationId,
  type ISODateTime,
  type JsonValue,
  type Result,
} from "@kanbien/core/shared";
import type {
  PlatformApp,
  PlatformJobName,
  PlatformJobRegistration,
  PlatformMountDeps,
} from "@kanbien/platform-contracts";
import {
  createPlatformRuntimeJobContext,
  createPlatformRuntimeLifecycle,
  mountPlatformRuntimeApps,
  type PlatformRuntimeLifecycleController,
  type PlatformRuntimeMountResult,
} from "@kanbien/platform-runtime";

export type PlatformWorkerErrorCode =
  | "PLATFORM_WORKER_MOUNT_FAILED"
  | "PLATFORM_WORKER_QUEUE_CLOSED"
  | "PLATFORM_WORKER_NOT_READY"
  | "PLATFORM_WORKER_JOB_NOT_FOUND"
  | "PLATFORM_WORKER_INVALID_PAYLOAD"
  | "PLATFORM_WORKER_HANDLER_FAILED"
  | "PLATFORM_WORKER_IDEMPOTENCY_FAILED";

export interface PlatformWorkerError {
  readonly code: PlatformWorkerErrorCode;
  readonly defaultMessage: string;
  readonly details?: Readonly<Record<string, JsonValue>>;
  readonly cause?: unknown;
}

export interface PlatformWorkerQueueEntry {
  readonly message: QueueMessage;
  readonly attempt: number;
  readonly enqueuedAt: ISODateTime;
  readonly delayMs?: number;
}

export interface PlatformWorkerDeadLetter {
  readonly message: QueueMessage;
  readonly attempts: number;
  readonly failedAt: ISODateTime;
  readonly error: PlatformWorkerError;
}

export interface PlatformWorkerQueue {
  enqueue(message: QueueMessage): Result<void, PlatformWorkerError>;
  next(): PlatformWorkerQueueEntry | undefined;
  retry(entry: PlatformWorkerQueueEntry, delayMs: number): Result<void, PlatformWorkerError>;
  deadLetter(entry: PlatformWorkerQueueEntry, error: PlatformWorkerError): void;
  pending(): readonly PlatformWorkerQueueEntry[];
  deadLetters(): readonly PlatformWorkerDeadLetter[];
  close(): void;
  isClosed(): boolean;
}

export interface PlatformWorkerIdempotencyStore {
  hasProcessed(key: string): Promise<boolean> | boolean;
  recordProcessed(key: string): Promise<void> | void;
}

export type PlatformWorkerRunStatus = "idle" | "succeeded" | "retry" | "dead-lettered";
export type PlatformWorkerIdempotencyOutcome = "none" | "processed" | "skipped";

export type PlatformWorkerRunNextResult =
  | {
      readonly status: "idle";
    }
  | {
      readonly status: "succeeded";
      readonly jobName: PlatformJobName;
      readonly message: QueueMessage;
      readonly attempt: number;
      readonly idempotency: PlatformWorkerIdempotencyOutcome;
    }
  | {
      readonly status: "retry";
      readonly jobName?: PlatformJobName;
      readonly message: QueueMessage;
      readonly attempt: number;
      readonly nextAttempt: number;
      readonly delayMs: number;
      readonly error: PlatformWorkerError;
    }
  | {
      readonly status: "dead-lettered";
      readonly jobName?: PlatformJobName;
      readonly message: QueueMessage;
      readonly attempt: number;
      readonly error: PlatformWorkerError;
    };

export interface PlatformWorkerShellOptions {
  readonly apps: readonly PlatformApp[];
  readonly deps: PlatformMountDeps;
  readonly queue?: PlatformWorkerQueue;
  readonly idempotency?: PlatformWorkerIdempotencyStore;
  readonly maxAttempts?: number;
  readonly retryBackoffMs?: (attempt: number) => number;
}

export interface PlatformWorkerRunUntilIdleOptions {
  readonly maxIterations?: number;
}

export interface PlatformWorkerShell {
  readonly mounted: PlatformRuntimeMountResult;
  readonly queue: PlatformWorkerQueue;
  readonly lifecycle: PlatformRuntimeLifecycleController;
  start(): Promise<Result<void, PlatformWorkerError>>;
  enqueue(message: QueueMessage): Result<void, PlatformWorkerError>;
  runNext(): Promise<Result<PlatformWorkerRunNextResult, PlatformWorkerError>>;
  runUntilIdle(options?: PlatformWorkerRunUntilIdleOptions): Promise<Result<readonly PlatformWorkerRunNextResult[], PlatformWorkerError>>;
  shutdown(): Promise<Result<void, PlatformWorkerError>>;
}

export function createInMemoryPlatformWorkerQueue(input: {
  readonly now?: () => ISODateTime;
} = {}): PlatformWorkerQueue {
  const now = input.now ?? (() => defaultNow);
  const pending: PlatformWorkerQueueEntry[] = [];
  const deadLetters: PlatformWorkerDeadLetter[] = [];
  let closed = false;

  return {
    enqueue(message) {
      if (closed) {
        return workerFailure("PLATFORM_WORKER_QUEUE_CLOSED", "Worker queue is closed.");
      }

      pending.push({ message, attempt: 1, enqueuedAt: now() });
      return workerSuccess();
    },
    next() {
      return pending.shift();
    },
    retry(entry, delayMs) {
      if (closed) {
        return workerFailure("PLATFORM_WORKER_QUEUE_CLOSED", "Worker queue is closed.");
      }

      pending.push({
        message: entry.message,
        attempt: entry.attempt + 1,
        enqueuedAt: now(),
        delayMs,
      });
      return workerSuccess();
    },
    deadLetter(entry, error) {
      deadLetters.push({
        message: entry.message,
        attempts: entry.attempt,
        failedAt: now(),
        error,
      });
    },
    pending: () => pending.map(copyQueueEntry),
    deadLetters: () => deadLetters.map(copyDeadLetter),
    close() {
      closed = true;
    },
    isClosed: () => closed,
  };
}

export function createInMemoryPlatformWorkerIdempotencyStore(): PlatformWorkerIdempotencyStore {
  const processed = new Set<string>();

  return {
    hasProcessed: (key) => processed.has(key),
    recordProcessed: (key) => {
      processed.add(key);
    },
  };
}

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

  const queue = options.queue ?? createInMemoryPlatformWorkerQueue({
    now: () => isoDateTimeFromDate(options.deps.clock.now()),
  });
  const lifecycle = createPlatformRuntimeLifecycle({ apps: mounted.value.apps });
  const jobsByMessageType = new Map(mounted.value.jobs.map((job) => [String(job.messageType), job]));
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
      recordWorkerAttempt(options, "dead-lettered");
      return { ok: true, value: deadLettered(entry, error) };
    }

    const invalidPayload = validateJobPayload(job, entry.message);
    if (invalidPayload !== undefined) {
      queue.deadLetter(entry, invalidPayload);
      recordWorkerAttempt(options, "dead-lettered");
      return { ok: true, value: deadLettered(entry, invalidPayload, job.name) };
    }

    const idempotencyKey = entry.message.idempotencyKey === undefined ? undefined : String(entry.message.idempotencyKey);
    if (idempotencyKey !== undefined && options.idempotency !== undefined) {
      try {
        if (await options.idempotency.hasProcessed(idempotencyKey)) {
          recordWorkerAttempt(options, "succeeded");
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
        return workerFailure("PLATFORM_WORKER_IDEMPOTENCY_FAILED", "Worker idempotency lookup failed.", { key: idempotencyKey }, error);
      }
    }

    try {
      const context = createPlatformRuntimeJobContext({
        jobName: job.name,
        message: entry.message,
        correlationId: entry.message.correlationId ?? correlationId(String(entry.message.id)),
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

      options.deps.logger.write({
        level: "info",
        message: "platform.worker.job.succeeded",
        fields: { jobName: String(job.name), messageType: String(entry.message.type), attempt: entry.attempt },
      });
      recordWorkerAttempt(options, "succeeded");
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
          return retry;
        }

        options.deps.logger.write({
          level: "warn",
          message: "platform.worker.job.retry",
          fields: { jobName: String(job.name), messageType: String(entry.message.type), attempt: entry.attempt, nextAttempt: entry.attempt + 1, delayMs },
        });
        recordWorkerAttempt(options, "retry");
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
      options.deps.logger.write({
        level: "error",
        message: "platform.worker.job.dead_lettered",
        fields: { jobName: String(job.name), messageType: String(entry.message.type), attempt: entry.attempt },
      });
      recordWorkerAttempt(options, "dead-lettered");
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

function recordWorkerAttempt(options: PlatformWorkerShellOptions, status: Exclude<PlatformWorkerRunStatus, "idle">): void {
  options.deps.metrics.record({
    name: metricName("platform.worker.job.attempt"),
    kind: "counter",
    value: 1,
    unit: metricUnit("count"),
    recordedAt: isoDateTimeFromDate(options.deps.clock.now()),
    labels: { status },
  });
}

function workerSuccess(): Result<void, PlatformWorkerError> {
  return { ok: true, value: undefined };
}

function workerFailure(
  code: PlatformWorkerErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): Result<never, PlatformWorkerError> {
  return {
    ok: false,
    error: workerError(code, defaultMessage, details, cause),
  };
}

function workerError(
  code: PlatformWorkerErrorCode,
  defaultMessage: string,
  details?: Readonly<Record<string, JsonValue>>,
  cause?: unknown,
): PlatformWorkerError {
  return {
    code,
    defaultMessage,
    ...(details === undefined ? {} : { details }),
    ...(cause === undefined ? {} : { cause }),
  };
}

function copyQueueEntry(entry: PlatformWorkerQueueEntry): PlatformWorkerQueueEntry {
  return { ...entry };
}

function copyDeadLetter(deadLetter: PlatformWorkerDeadLetter): PlatformWorkerDeadLetter {
  return {
    ...deadLetter,
    error: { ...deadLetter.error },
  };
}

const defaultNow = "2026-07-10T00:00:00.000Z" as ISODateTime;
