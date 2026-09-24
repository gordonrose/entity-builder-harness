import { noopTracer, type TraceSpan, type TraceSpanOutcome } from "@kanbien/core/monitoring";
import { outboxEntryId, type OutboxEntryId } from "@kanbien/core/persistence";
import type { QueueMessage } from "@kanbien/core/queues";
import { causationId, correlationId, isoDateTimeFromDate, type Result } from "@kanbien/core/shared";
import {
  recordPlatformPersistenceObservation,
  type PlatformPersistenceTransition,
  type PlatformPersistenceTransitionOutcome,
} from "@kanbien/platform-persistence";
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
  PlatformWorkerDurableOutboxProcessingOptions,
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

  if (options.durableOutboxProcessing !== undefined && (!Number.isInteger(options.durableOutboxProcessing.leaseDurationMs) || options.durableOutboxProcessing.leaseDurationMs <= 0)) {
    return workerFailure(
      "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
      "Durable outbox processing requires a positive lease duration.",
      { phase: "configuration" },
    );
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

    const durableClaim = await claimDurableOutboxProcessing(options, entry.message);
    if (!durableClaim.ok) {
      recordDurablePersistenceObservation(
        options,
        entry.message,
        traceSpan,
        durableTransitionForClaimError(durableClaim.error),
        durableOutcomeForClaimError(durableClaim.error),
        durableClaim.error,
      );
      if (durableClaim.error.code === "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID") {
        queue.deadLetter(entry, durableClaim.error);
        recordWorkerObservation(options, entry, profile, startedAt, {
          outcome: "rejected",
          deliveryDisposition: "dead_lettered",
          error: durableClaim.error,
        });
        endWorkerTrace(profile, traceSpan, {
          outcome: "rejected",
          deliveryDisposition: "dead_lettered",
          error: durableClaim.error,
        });
        return { ok: true, value: deadLettered(entry, durableClaim.error, job.name) };
      }

      recordWorkerObservation(options, entry, profile, startedAt, { outcome: "failed", error: durableClaim.error });
      endWorkerTrace(profile, traceSpan, { outcome: "failed", error: durableClaim.error });
      return durableClaim;
    }

    if (durableClaim.value.kind === "already-completed") {
      if (durableClaim.value.outcome === "terminal-failure") {
        const terminalFailure = workerError(
          "PLATFORM_WORKER_DURABLE_PROCESSING_TERMINAL_FAILURE",
          "Durable outbox processing previously reached a terminal failure.",
        );
        recordDurablePersistenceObservation(
          options,
          entry.message,
          traceSpan,
          "processing.duplicate_terminal_failure",
          "failed",
          terminalFailure,
        );
        queue.deadLetter(entry, terminalFailure);
        recordWorkerObservation(options, entry, profile, startedAt, {
          outcome: "failed",
          deliveryDisposition: "dead_lettered",
          error: terminalFailure,
        });
        endWorkerTrace(profile, traceSpan, {
          outcome: "failed",
          deliveryDisposition: "dead_lettered",
          error: terminalFailure,
        });
        return { ok: true, value: deadLettered(entry, terminalFailure, job.name) };
      }

      recordDurablePersistenceObservation(
        options,
        entry.message,
        traceSpan,
        "processing.duplicate_succeeded",
        "succeeded",
      );

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
          idempotency: "durable-skipped",
        },
      };
    }

    if (durableClaim.value.kind === "claimed") {
      recordDurablePersistenceObservation(
        options,
        entry.message,
        traceSpan,
        "processing.claimed",
        "succeeded",
      );
    }

    const idempotencyKey = options.durableOutboxProcessing === undefined
      ? (entry.message.idempotencyKey === undefined ? undefined : String(entry.message.idempotencyKey))
      : undefined;
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

      if (durableClaim.value.kind === "claimed") {
        const completed = await options.durableOutboxProcessing!.processingStore.complete({
          outboxEntryId: durableClaim.value.outboxEntryId,
          fence: durableClaim.value.fence,
          outcome: "succeeded",
          completedAt: isoDateTimeFromDate(options.deps.clock.now()),
        });
        if (!completed.ok) {
          const completionError = durableProcessingFailure("complete", completed.error);
          recordDurablePersistenceObservation(
            options,
            entry.message,
            traceSpan,
            "processing.completion_failed",
            "failed",
            completionError,
          );
          recordWorkerObservation(options, entry, profile, startedAt, { outcome: "failed", error: completionError, handlerStarted: true });
          endWorkerTrace(profile, traceSpan, { outcome: "failed", error: completionError, handlerStarted: true });
          return { ok: false, error: completionError };
        }

        recordDurablePersistenceObservation(
          options,
          entry.message,
          traceSpan,
          "processing.completed",
          "succeeded",
        );
      }

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
          idempotency: durableClaim.value.kind === "claimed"
            ? "durable-processed"
            : (idempotencyKey === undefined ? "none" : "processed"),
        },
      };
    } catch (error) {
      const workerHandlerError = workerError("PLATFORM_WORKER_HANDLER_FAILED", "Platform job handler failed.", {
        jobName: String(job.name),
        messageType: String(entry.message.type),
        attempt: entry.attempt,
      }, error);

      if (durableClaim.value.kind === "claimed") {
        const settled = await settleFailedDurableOutboxProcessing({
          processing: options.durableOutboxProcessing!,
          outboxEntryId: durableClaim.value.outboxEntryId,
          fence: durableClaim.value.fence,
          terminal: entry.attempt >= maxAttempts,
          now: options.deps.clock.now(),
        });
        if (!settled.ok) {
          recordDurablePersistenceObservation(
            options,
            entry.message,
            traceSpan,
            "processing.settlement_failed",
            "failed",
            settled.error,
          );
          recordWorkerObservation(options, entry, profile, startedAt, { outcome: "failed", error: settled.error, handlerStarted: true });
          endWorkerTrace(profile, traceSpan, { outcome: "failed", error: settled.error, handlerStarted: true });
          return settled;
        }

        recordDurablePersistenceObservation(
          options,
          entry.message,
          traceSpan,
          entry.attempt >= maxAttempts ? "processing.terminal_failure_recorded" : "processing.retry_released",
          "failed",
          workerHandlerError,
        );
      }

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

type DurableOutboxClaim =
  | { readonly kind: "not-configured" }
  | {
      readonly kind: "already-completed";
      readonly outboxEntryId: OutboxEntryId;
      readonly outcome: import("@kanbien/platform-persistence").PlatformProcessingOutcome;
    }
  | { readonly kind: "claimed"; readonly outboxEntryId: OutboxEntryId; readonly fence: import("@kanbien/platform-persistence").PlatformPersistenceFence };

async function claimDurableOutboxProcessing(
  options: PlatformWorkerShellOptions,
  message: QueueMessage,
): Promise<Result<DurableOutboxClaim, PlatformWorkerError>> {
  const processing = options.durableOutboxProcessing;
  if (processing === undefined) {
    return { ok: true, value: { kind: "not-configured" } };
  }

  const identity = durableOutboxEntryId(message);
  if (!identity.ok) {
    return identity;
  }

  try {
    const claim = await processing.processingStore.claim({
      outboxEntryId: identity.value,
      owner: processing.owner,
      acquiredAt: isoDateTimeFromDate(options.deps.clock.now()),
      leaseDurationMs: processing.leaseDurationMs,
    });
    if (!claim.ok) {
      return { ok: false, error: durableProcessingFailure("claim", claim.error) };
    }

    if (claim.value.disposition === "already-completed") {
      const outcome = claim.value.record.completion?.outcome;
      if (outcome === undefined) {
        return {
          ok: false,
          error: workerError(
            "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
            "Completed durable outbox processing did not supply a completion outcome.",
            { phase: "claim" },
          ),
        };
      }
      return { ok: true, value: { kind: "already-completed", outboxEntryId: identity.value, outcome } };
    }

    if (claim.value.disposition === "lease-active") {
      return {
        ok: false,
        error: workerError(
          "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY",
          "Durable outbox processing is already claimed by another worker.",
          { phase: "claim" },
        ),
      };
    }

    const lease = claim.value.record.lease;
    if (lease === undefined) {
      return {
        ok: false,
        error: workerError(
          "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
          "Durable outbox processing claim did not supply a lease.",
          { phase: "claim" },
        ),
      };
    }

    return { ok: true, value: { kind: "claimed", outboxEntryId: identity.value, fence: lease.fence } };
  } catch (error) {
    return {
      ok: false,
      error: workerError(
        "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
        "Durable outbox processing claim failed.",
        { phase: "claim" },
        error,
      ),
    };
  }
}

function durableOutboxEntryId(message: QueueMessage): Result<OutboxEntryId, PlatformWorkerError> {
  const payload = message.payload;
  if (!isRecord(payload) || typeof payload.outboxEntryId !== "string" || payload.outboxEntryId.length === 0) {
    return durableOutboxEnvelopeFailure();
  }

  const outboxId = payload.outboxEntryId;
  if (String(message.id) !== outboxId || String(message.idempotencyKey ?? "") !== outboxId) {
    return durableOutboxEnvelopeFailure();
  }

  return { ok: true, value: outboxEntryId(outboxId) };
}

function durableOutboxEnvelopeFailure(): Result<never, PlatformWorkerError> {
  return {
    ok: false,
    error: workerError(
      "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID",
      "Durable outbox delivery must preserve one stable outbox identity.",
    ),
  };
}

function recordDurablePersistenceObservation( // Emit safe durable-processing transition evidence without making worker delivery depend on telemetry.
  options: PlatformWorkerShellOptions, // Read the optional durable-outbox composition selected for this worker shell.
  message: QueueMessage, // Read only the message's safe correlation and trace continuity references.
  traceSpan: TraceSpan | undefined, // Reuse the enclosing worker span as a parent when tracing was enabled.
  transition: PlatformPersistenceTransition, // Name the closed durable-processing transition that occurred.
  outcome: PlatformPersistenceTransitionOutcome, // Preserve the bounded transition outcome.
  error?: PlatformWorkerError, // Allow the observer to reduce a worker failure to its stable error classification.
): void { // Keep telemetry strictly best effort through the persistence observer boundary.
  recordPlatformPersistenceObservation(options.durableOutboxProcessing?.observer, { // Delegate to the provider-neutral no-throw persistence observation helper.
    transition, // Preserve the stable transition identity.
    outcome, // Preserve the bounded logical outcome.
    ...(message.correlationId === undefined ? {} : { correlationId: message.correlationId }), // Carry correlation only for the observer's log envelope, never metric labels or trace attributes.
    ...(traceSpan === undefined ? {} : { traceParent: traceSpan.context }), // Nest the transition span below the worker-delivery span when one exists.
    ...(error === undefined ? {} : { error }), // Let the selected observer emit only a normalised error class.
  }); // Finish the best-effort observation request.
}

function durableTransitionForClaimError( // Map one durable claim failure to the precise fixed transition that operators need to distinguish.
  error: PlatformWorkerError, // Read the stable worker error code without inspecting error messages or payloads.
): PlatformPersistenceTransition { // Return one closed persistence transition name.
  if (error.code === "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID") { // Identify a malformed or unstable three-part outbox identity.
    return "processing.envelope_rejected"; // Record the safe pre-handler rejection transition.
  }

  if (error.code === "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY") { // Identify a delivery that encountered an active durable claim.
    return "processing.lease_active"; // Record the legitimate coordination contention transition.
  }

  return "processing.claim_failed"; // Treat every remaining durable-store or internal failure as a failed claim.
}

function durableOutcomeForClaimError( // Map one durable claim failure into the bounded transition outcome vocabulary.
  error: PlatformWorkerError, // Read the stable error code already produced by the worker boundary.
): PlatformPersistenceTransitionOutcome { // Return a controlled observability outcome rather than a transport status.
  if (
    error.code === "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID"
    || error.code === "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY"
  ) { // Treat invalid identity and active lease as controlled precondition rejections.
    return "rejected"; // Keep these distinct from unexpected persistence failure.
  }

  return "failed"; // Treat all other durable claim failures as failed transitions.
}

async function settleFailedDurableOutboxProcessing(input: {
  readonly processing: PlatformWorkerDurableOutboxProcessingOptions;
  readonly outboxEntryId: OutboxEntryId;
  readonly fence: import("@kanbien/platform-persistence").PlatformPersistenceFence;
  readonly terminal: boolean;
  readonly now: Date;
}): Promise<Result<void, PlatformWorkerError>> {
  try {
    const settled = input.terminal
      ? await input.processing.processingStore.complete({
        outboxEntryId: input.outboxEntryId,
        fence: input.fence,
        outcome: "terminal-failure",
        completedAt: isoDateTimeFromDate(input.now),
      })
      : await input.processing.processingStore.release({
        outboxEntryId: input.outboxEntryId,
        fence: input.fence,
        releasedAt: isoDateTimeFromDate(input.now),
      });
    if (!settled.ok) {
      return { ok: false, error: durableProcessingFailure(input.terminal ? "complete" : "release", settled.error) };
    }
    return { ok: true, value: undefined };
  } catch (error) {
    return {
      ok: false,
      error: workerError(
        "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
        "Durable outbox processing settlement failed.",
        { phase: input.terminal ? "complete" : "release" },
        error,
      ),
    };
  }
}

function durableProcessingFailure(
  phase: "claim" | "complete" | "release",
  error: { readonly code: string },
): PlatformWorkerError {
  return workerError(
    "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
    "Durable outbox processing could not record its required state.",
    { phase, persistenceCode: error.code },
    error,
  );
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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
