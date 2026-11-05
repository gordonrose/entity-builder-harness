import { noopTracer, type TraceSpan, type TraceSpanOutcome } from "@kanbien/core/monitoring";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { createDiagnosticRecord, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { outboxEntryId, type OutboxEntryId } from "@kanbien/core/persistence";
import { validationDiagnostic } from "@kanbien/core/validation";
import type { QueueMessage } from "@kanbien/core/queues";
import { causationId, correlationId, isoDateTimeFromDate, type Result } from "@kanbien/core/shared";
import {
  recordPlatformPersistenceObservation,
  validatePersistenceLeaseDuration,
  type PlatformPersistenceTransition,
  type PlatformPersistenceTransitionOutcome,
} from "@kanbien/platform-persistence";
import { tenantContext } from "@kanbien/core/tenancy";
import {
  platformProfileAllowsSignal,
  platformErrorClassDeclarations,
  platformProfileLogFields,
  platformProfileMeasuresLatency,
  platformProfileMetricLabels,
  platformProfileTraceFields,
  platformContractDiagnosticCatalog,
} from "@kanbien/platform-contracts";
import type {
  PlatformCapabilityObservabilityProfile,
  PlatformDiagnosticReporter,
  PlatformDiagnosticCatalog,
  PlatformDiagnosticContext,
  PlatformJobDeliveryDisposition,
  PlatformJobName,
  PlatformJobRegistration,
  PlatformOperationalNomenclature,
} from "@kanbien/platform-contracts";
import { assertPlatformConfigValid, platformConfigDiagnosticCatalog } from "@kanbien/platform-config";
import { platformHealthDiagnosticCatalog, platformReadiness } from "@kanbien/platform-health";
import {
  elapsedMilliseconds,
  endPlatformTraceSpan,
  platformErrorClass,
  recordPlatformMetric,
  startPlatformTraceSpan,
  writePlatformLog,
  createPlatformDiagnosticReporter,
  createPlatformMetricDiagnosticBinding,
  platformObservabilityDiagnosticCatalog,
  type PlatformMetricDiagnosticBinding,
  reportPlatformErrorDiagnostic,
  reportPlatformDiagnostic,
  type PlatformObservationDiagnostics,
} from "@kanbien/platform-observability";
import {
  createPlatformRuntimeJobContext,
  createPlatformRuntimeLifecycle,
  mountPlatformRuntimeApps,
  platformRuntimeDiagnosticCatalog,
} from "@kanbien/platform-runtime";
import { workerError, workerFailure, type PlatformWorkerError } from "./errors";
import { captureWorkerDiagnostic, platformWorkerDiagnosticCatalog, platformWorkerBoundaryDiagnostic, reportWorkerBoundary, workerDiagnosticEvidence,
  workerDeliveryRejectedRecord, workerCoordinationRecord, workerDeliveryBoundaryRecord, type WorkerDeliveryBoundaryDetail } from "./diagnostics";
import { workerDiagnosticErrorCodes } from "./diagnostics";
import { workerConfigurationDiagnosticRecord } from "./configuration-diagnostics";
import { validateWorkerRetryConfiguration, validateWorkerRetryDelay, workerRetryDelayError } from "./configuration/index";
import { createInMemoryPlatformWorkerQueue, workerQueueNow } from "./queue";
import type {
  PlatformWorkerQueueEntry,
  PlatformWorkerDurableOutboxProcessingOptions,
  PlatformWorkerRunNextResult,
  PlatformWorkerShell,
  PlatformWorkerShellOptions,
} from "./types";

export const workerBuiltinDiagnosticCatalogs = Object.freeze([coreDiagnosticCatalog, platformContractDiagnosticCatalog,
  platformWorkerDiagnosticCatalog, platformRuntimeDiagnosticCatalog, platformConfigDiagnosticCatalog,
  platformObservabilityDiagnosticCatalog, platformHealthDiagnosticCatalog]);

export async function createPlatformWorkerShell(
  options: PlatformWorkerShellOptions,
): Promise<Result<PlatformWorkerShell, PlatformWorkerError>> {
  let startupCatalogs: readonly PlatformDiagnosticCatalog[] = [];
  function diagnosticDefinitions(): readonly DiagnosticDefinition[] {
    try { return [...workerBuiltinDiagnosticCatalogs, ...(options.diagnosticCatalogs ?? []), ...startupCatalogs].flatMap((catalog) => catalog.definitions); }
    catch { return []; }
  }
  let selectedStartupReporter: PlatformDiagnosticReporter | undefined;
  const startupDiagnostics: PlatformDiagnosticReporter = { report(record, context) {
    if (selectedStartupReporter === undefined) {
      const builtins = workerBuiltinDiagnosticCatalogs;
      try { selectedStartupReporter = options.deps.diagnostics ?? createPlatformDiagnosticReporter({
        catalogs: [...builtins, ...(options.diagnosticCatalogs ?? []), ...startupCatalogs], logger: options.deps.logger, clock: options.deps.clock,
      }); } catch (error) {
        try {
          selectedStartupReporter = createPlatformDiagnosticReporter({ catalogs: builtins, logger: options.deps.logger, clock: options.deps.clock });
          reportPlatformErrorDiagnostic(selectedStartupReporter, error, { capability: "platform-contracts", operation: "select-diagnostic-catalog", stage: "configuration" });
        } catch { return { status: "unavailable" }; }
      }
    }
    try { return selectedStartupReporter.report(record, context); } catch { return { status: "unavailable" }; }
  } };
  const mounted = await mountPlatformRuntimeApps({
    apps: options.apps,
    deps: options.deps,
    get diagnosticDefinitions() { return diagnosticDefinitions(); },
    onDiagnostic(record, context, registeredCatalogs) {
      if (registeredCatalogs !== undefined) startupCatalogs = registeredCatalogs;
      reportPlatformDiagnostic(startupDiagnostics, record, context);
    },
  });

  if (!mounted.ok) {
    for (const error of mounted.error.contractErrors) reportPlatformErrorDiagnostic(startupDiagnostics, error,
      { capability: "platform-contracts", operation: "register", stage: "configuration" });
    return workerFailure("PLATFORM_WORKER_MOUNT_FAILED", "Platform worker failed to mount apps.", { runtimeCode: mounted.error.code }, mounted.error, diagnosticDefinitions());
  }

  startupCatalogs = mounted.value.diagnosticCatalogs;

  const config = assertPlatformConfigValid({
    source: options.deps.config,
    schemas: mounted.value.configSchemas,
    get diagnosticDefinitions() { return diagnosticDefinitions(); },
    onDiagnostic: (record) => reportPlatformDiagnostic(startupDiagnostics, record, { capability: "platform-config", operation: "validate-schema", stage: "configuration" }),
  });
  if (!config.ok) {
    return workerFailure("PLATFORM_WORKER_CONFIG_INVALID", "Platform worker config validation failed before polling.", config.error.details, config.error, diagnosticDefinitions());
  }

  const processing = options.durableOutboxProcessing;
  const lease = processing === undefined ? undefined : validatePersistenceLeaseDuration(processing.leaseDurationMs);
  if (lease !== undefined && !lease.ok) {
    const error = { ...workerError(
      "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
      "Durable outbox processing requires a positive lease duration.",
      { phase: "configuration" },
    ), diagnosticRecord: workerConfigurationDiagnosticRecord("durable-lease-duration", lease.error.reason) };
    reportPlatformErrorDiagnostic(startupDiagnostics, error, { capability: "platform-worker", operation: "configure", stage: "configuration" });
    return { ok: false, error };
  }

  const retryConfiguration = validateWorkerRetryConfiguration(options);
  if (!retryConfiguration.ok) {
    const error = workerError("PLATFORM_WORKER_CONFIG_INVALID", "Worker retry configuration is invalid.", undefined, undefined, [], retryConfiguration.error.diagnosticRecord);
    reportPlatformErrorDiagnostic(startupDiagnostics, error, { capability: "platform-worker", operation: "configure", stage: "configuration" });
    return { ok: false, error };
  }
  const checkedProcessing: PlatformWorkerDurableOutboxProcessingOptions | undefined = processing === undefined || lease === undefined || !lease.ok ? undefined : Object.freeze({
    get processingStore() { return processing.processingStore; },
    get owner() { return processing.owner; },
    get observer() { return processing.observer; },
    leaseDurationMs: lease.value,
  }) as PlatformWorkerDurableOutboxProcessingOptions;
  const queue = options.queue ?? createInMemoryPlatformWorkerQueue({
    now: workerQueueNow(options.deps.clock),
  });
  const lifecycle = createPlatformRuntimeLifecycle({ apps: mounted.value.apps,
    get diagnosticDefinitions() { return diagnosticDefinitions(); },
    onDiagnostic: (record, context) => reportPlatformDiagnostic(startupDiagnostics, record, context),
  });
  const jobsByMessageType = new Map(mounted.value.jobs.map((job) => [String(job.messageType), job]));
  const profilesByName = new Map(mounted.value.observabilityProfiles.map((profile) => [String(profile.name), profile]));
  let diagnostics: PlatformDiagnosticReporter;
  try {
    diagnostics = options.deps.diagnostics ?? createPlatformDiagnosticReporter({
      catalogs: [...workerBuiltinDiagnosticCatalogs, ...(options.diagnosticCatalogs ?? []), ...mounted.value.diagnosticCatalogs],
      logger: options.deps.logger, clock: options.deps.clock,
    });
  } catch (error) {
    try { reportPlatformErrorDiagnostic(createPlatformDiagnosticReporter({ catalogs: [platformContractDiagnosticCatalog], logger: options.deps.logger, clock: options.deps.clock }), error,
      { capability: "platform-contracts", operation: "select-diagnostic-catalog", stage: "configuration" }); } catch { /* Optional delivery only. */ }
    return workerFailure("PLATFORM_WORKER_MOUNT_FAILED", "Platform worker diagnostic catalog selection is invalid.");
  }
  // Preserve the old eager copy of other options, without rereading checked inputs.
  const copiedOptions = Object.fromEntries(Reflect.ownKeys(options)
    .filter(key => Object.prototype.propertyIsEnumerable.call(options, key)
      && key !== "maxAttempts" && key !== "retryBackoffMs" && key !== "durableOutboxProcessing")
    .map(key => [key, Reflect.get(options, key)]));
  options = {
    ...copiedOptions,
    deps: { ...options.deps, diagnostics },
    maxAttempts: retryConfiguration.value.maxAttempts,
    retryBackoffMs: retryConfiguration.value.retryBackoffMs,
    durableOutboxProcessing: checkedProcessing,
  } as PlatformWorkerShellOptions;
  const metricDiagnostics = createPlatformMetricDiagnosticBinding(diagnostics, { capability: "platform-worker", stage: "request" });
  const tracer = options.tracer ?? noopTracer;
  const { maxAttempts, retryBackoffMs } = retryConfiguration.value;

  async function runNext(): Promise<Result<PlatformWorkerRunNextResult, PlatformWorkerError>> {
    let profile: PlatformCapabilityObservabilityProfile | undefined;
    let phase: WorkerDeliveryBoundaryDetail["phase"] = "dequeue";
    let effect: WorkerDeliveryBoundaryDetail["effect"] = "handler-not-invoked";
    let rawBoundaryReported = false;
    const reportedErrors = new WeakSet<object>();
    function observe(own: DiagnosticRecord, cause?: unknown): void {
      try {
        if (profile === undefined || !platformProfileAllowsSignal(profile, "operational_log")) return;
        const context: PlatformDiagnosticContext = { capability: "platform-worker", operation: "job-delivery", stage: "request" };
        reportPlatformDiagnostic(diagnostics, own, context);
        const notices: DiagnosticRecord[] = [];
        const evidence = workerDiagnosticEvidence(cause, diagnosticDefinitions(), record => notices.push(record));
        if (evidence.diagnosticRecord !== undefined) reportPlatformDiagnostic(diagnostics, evidence.diagnosticRecord, context);
        for (const source of evidence.relatedDiagnosticRecords ?? []) reportPlatformDiagnostic(diagnostics, source, context);
        for (const record of notices) reportPlatformDiagnostic(diagnostics, record, context);
      } catch { /* Observation cannot affect delivery or settlement. */ }
    }
    const boundary: WorkerBoundaryObserver = (at, reason, cause, knownEffect = effect) => {
      const own = captureWorkerDiagnostic(() => workerDeliveryBoundaryRecord({ operation: "job-delivery", phase: at, reason, effect: knownEffect }));
      observe(own, cause); return own;
    };
    function recordWorkerObservation(...args: Parameters<typeof recordWorkerObservationUnchecked>): void {
      const event = args[5];
      recordWorkerObservationUnchecked(args[0], args[1], args[2], args[3], args[4],
        { ...event, ...(event.error !== undefined && reportedErrors.has(event.error) ? { diagnosticAlreadyReported: true } : {}) }, observationDiagnostics(args[3]));
    }
    function observationDiagnostics(selectedProfile: PlatformCapabilityObservabilityProfile | undefined): PlatformObservationDiagnostics | undefined {
      try {
        if (selectedProfile === undefined || !platformProfileAllowsSignal(selectedProfile, "operational_log")) return undefined;
        return { reporter: diagnostics, get definitions() { return diagnosticDefinitions(); },
          context: { capability: "platform-worker", operation: "job-observation", stage: "request" } };
      } catch { return undefined; }
    }
    function endWorkerTrace(...args: Parameters<typeof endWorkerTraceUnchecked>): void {
      endWorkerTraceUnchecked(args[0], args[1], args[2], observationDiagnostics(args[0]));
    }
    try {
    if (!lifecycle.isReady()) {
      return workerFailure("PLATFORM_WORKER_NOT_READY", "Platform worker shell is not ready.", undefined, undefined, [], captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ field: "lifecycle", condition: "not-ready", effect: "handler-not-invoked" })));
    }

    const entry = queue.next();
    if (entry === undefined) {
      return { ok: true, value: { status: "idle" } };
    }

    phase = "selection";
    const job = jobsByMessageType.get(String(entry.message.type));
    if (job === undefined) {
      const error = workerError("PLATFORM_WORKER_JOB_NOT_FOUND", "No platform job is registered for the queue message type.", {
        messageType: String(entry.message.type),
      }, undefined, [], captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ field: "job", condition: "unmatched", effect: "handler-not-invoked" })));
      phase = "dead-letter";
      queue.deadLetter(entry, error);
      return { ok: true, value: deadLettered(entry, error) };
    }

    profile = workerProfileForJob(job, profilesByName);
    let startedAt: Date;
    try { startedAt = options.deps.clock.now(); }
    catch (error) {
      rawBoundaryReported = true;
      try {
        if (profile !== undefined && platformProfileAllowsSignal(profile, "operational_log")) reportWorkerBoundary(diagnostics,
          { operation: "job-delivery", phase: "delivery-clock", boundary: "selection-or-invocation", effect: "handler-not-invoked" }, error, diagnosticDefinitions());
      } catch { /* Optional delivery must not replace the original pre-context clock failure. */ }
      throw error;
    }
    const traceSpan = startWorkerTrace(tracer, entry, profile, observationDiagnostics(profile));

    phase = "validation";
    const invalidPayload = validateJobPayload(job, entry.message, diagnosticDefinitions, observe);
    if (invalidPayload !== undefined) {
      reportedErrors.add(invalidPayload);
      phase = "dead-letter";
      queue.deadLetter(entry, invalidPayload);
      phase = "observation";
      recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
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

    phase = "identity";
    const durableClaim = await claimDurableOutboxProcessing(options, entry.message, diagnosticDefinitions, boundary, observe);
    if (!durableClaim.ok) {
      reportedErrors.add(durableClaim.error);
      phase = "observation";
      recordDurablePersistenceObservation(
        options,
        entry.message,
        traceSpan,
        durableTransitionForClaimError(durableClaim.error),
        durableOutcomeForClaimError(durableClaim.error),
        durableClaim.error,
      );
      if (durableClaim.error.code === "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID") {
        observe(durableClaim.error.diagnosticRecord!);
        phase = "dead-letter";
        queue.deadLetter(entry, durableClaim.error);
        phase = "observation";
        recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
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

      recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, { outcome: "failed", error: durableClaim.error });
      endWorkerTrace(profile, traceSpan, { outcome: "failed", error: durableClaim.error });
      return durableClaim;
    }

    if (durableClaim.value.kind === "already-completed") {
      const condition = durableClaim.value.outcome === "terminal-failure" ? "already-terminal" : "already-completed";
      observe(captureWorkerDiagnostic(() => workerCoordinationRecord(condition)));
      phase = "observation";
      if (durableClaim.value.outcome === "terminal-failure") {
        const terminalFailure = workerError(
          "PLATFORM_WORKER_DURABLE_PROCESSING_TERMINAL_FAILURE",
          "Durable outbox processing previously reached a terminal failure.",
          undefined, undefined, [], captureWorkerDiagnostic(() => workerCoordinationRecord("already-terminal")),
        );
        recordDurablePersistenceObservation(
          options,
          entry.message,
          traceSpan,
          "processing.duplicate_terminal_failure",
          "failed",
          terminalFailure,
        );
        reportedErrors.add(terminalFailure);
        phase = "dead-letter";
        queue.deadLetter(entry, terminalFailure);
        phase = "observation";
        recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
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

      recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
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

    phase = "identity";
    const idempotencyKey = options.durableOutboxProcessing === undefined
      ? (entry.message.idempotencyKey === undefined ? undefined : String(entry.message.idempotencyKey))
      : undefined;
    if (idempotencyKey !== undefined && options.idempotency !== undefined) {
      try {
        phase = "lookup";
        if (await options.idempotency.hasProcessed(idempotencyKey)) {
          observe(captureWorkerDiagnostic(() => workerCoordinationRecord("idempotency-duplicate")));
          phase = "observation";
          recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
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
        const own = boundary(phase, "thrown", error, "handler-not-invoked");
        const idempotencyError = workerError(
          "PLATFORM_WORKER_IDEMPOTENCY_FAILED",
          "Worker idempotency lookup failed.",
          { key: idempotencyKey },
          error,
          diagnosticDefinitions(),
          own,
        );
        reportedErrors.add(idempotencyError);
        phase = "observation";
        recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, { outcome: "failed", error: idempotencyError });
        endWorkerTrace(profile, traceSpan, { outcome: "failed", error: idempotencyError });
        return { ok: false, error: idempotencyError };
      }
    }

    let contextDiagnostic: { readonly record: DiagnosticRecord; readonly context: PlatformDiagnosticContext } | undefined;
    let contextInputComplete = false;
    try {
      phase = "context";
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
        onDiagnostic: (contextInputComplete = true, (record, context) => { contextDiagnostic = { record, context }; }),
      });
      phase = "handler"; effect = "handler-outcome-unknown";
      await job.handler.handle(entry.message, context);
      effect = "handler-succeeded";

      if (durableClaim.value.kind === "claimed") {
        phase = "complete";
        let completionStamp: ReturnType<typeof isoDateTimeFromDate>;
        const completed = await options.durableOutboxProcessing!.processingStore.complete({
          outboxEntryId: durableClaim.value.outboxEntryId,
          fence: durableClaim.value.fence,
          outcome: "succeeded",
          completedAt: (phase = "complete-clock", completionStamp = isoDateTimeFromDate(options.deps.clock.now()), phase = "complete", completionStamp),
        });
        if (!completed.ok) {
          const own = boundary("complete", "returned-failure", completed.error);
          const completionError = durableProcessingFailure("complete", completed.error, diagnosticDefinitions(), own);
          reportedErrors.add(completionError);
          phase = "observation";
          recordDurablePersistenceObservation(
            options,
            entry.message,
            traceSpan,
            "processing.completion_failed",
            "failed",
            completionError,
          );
          recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, { outcome: "failed", error: completionError, handlerStarted: true });
          endWorkerTrace(profile, traceSpan, { outcome: "failed", error: completionError, handlerStarted: true });
          return { ok: false, error: completionError };
        }

        phase = "observation";
        recordDurablePersistenceObservation(
          options,
          entry.message,
          traceSpan,
          "processing.completed",
          "succeeded",
        );
      }

      if (idempotencyKey !== undefined && options.idempotency !== undefined) {
        phase = "idempotency-record";
        await options.idempotency.recordProcessed(idempotencyKey);
      }

      phase = "observation";
      recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
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
      const failedPhase = phase;
      const own = phase === "context" ? undefined : boundary(phase, "thrown", error);
      if (!contextInputComplete) {
        try {
          const checked = createDiagnosticRecord(platformWorkerBoundaryDiagnostic, { operation: "job-delivery", phase: "context-input", boundary: "selection", effect: "handler-not-invoked" });
          if (checked.ok) contextDiagnostic = { record: checked.value, context: { capability: "platform-worker", operation: "job-delivery", stage: "request" } };
        } catch { /* Preserve the original argument-projection failure. */ }
      }
      const workerHandlerError = workerError("PLATFORM_WORKER_HANDLER_FAILED", "Platform job handler failed.", {
        jobName: String(job.name),
        messageType: String(entry.message.type),
        attempt: entry.attempt,
      }, error, diagnosticDefinitions(), contextDiagnostic?.record ?? own);
      if (own !== undefined) reportedErrors.add(workerHandlerError);
      let contextDiagnosticReported = false;
      try {
        if (contextDiagnostic !== undefined && profile !== undefined && platformProfileAllowsSignal(profile, "operational_log")) {
          contextDiagnosticReported = true;
          reportPlatformDiagnostic(diagnostics, contextDiagnostic.record, contextDiagnostic.context);
          const evidence = workerHandlerError.diagnosticRecord === contextDiagnostic.record
            ? { ...(workerHandlerError.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: workerHandlerError.relatedDiagnosticRecords }) } : workerHandlerError;
          reportPlatformErrorDiagnostic(diagnostics, evidence, contextDiagnostic.context);
        }
      } catch { /* Preserve existing cleanup even when optional observation is unavailable. */ }
      const contextEvidence = contextDiagnosticReported || own !== undefined ? { diagnosticAlreadyReported: true } : {};
      if (contextDiagnosticReported) reportedErrors.add(workerHandlerError);
      if (failedPhase === "handler") effect = "handler-failed";

      if (durableClaim.value.kind === "claimed") {
        phase = "settlement";
        const settled = await settleFailedDurableOutboxProcessing({
          processing: options.durableOutboxProcessing!,
          outboxEntryId: durableClaim.value.outboxEntryId,
          fence: durableClaim.value.fence,
          terminal: entry.attempt >= maxAttempts,
          now: (phase = "settlement-clock", options.deps.clock.now()),
        }, diagnosticDefinitions, boundary);
        if (!settled.ok) {
          reportedErrors.add(settled.error);
          phase = "observation";
          recordDurablePersistenceObservation(
            options,
            entry.message,
            traceSpan,
            "processing.settlement_failed",
            "failed",
            settled.error,
          );
          recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, { outcome: "failed", error: settled.error, handlerStarted: true });
          endWorkerTrace(profile, traceSpan, { outcome: "failed", error: settled.error, handlerStarted: true });
          return settled;
        }

        phase = "observation";
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
        phase = "backoff";
        const checkedDelay = validateWorkerRetryDelay(retryBackoffMs(entry.attempt));
        if (!checkedDelay.ok) {
          const invalidDelay = workerRetryDelayError(checkedDelay.error.reason);
          observe(invalidDelay.diagnosticRecord);
          rawBoundaryReported = true;
          throw invalidDelay;
        }
        const delayMs = checkedDelay.value;
        phase = "retry";
        const retry = queue.retry(entry, delayMs);
        if (!retry.ok) {
          boundary("retry", "returned-failure", retry.error);
          reportedErrors.add(retry.error);
          phase = "observation";
          recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, { outcome: "failed", error: retry.error, handlerStarted: true });
          endWorkerTrace(profile, traceSpan, { outcome: "failed", error: retry.error, handlerStarted: true });
          return retry;
        }

        phase = "observation";
        recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
          outcome: "failed",
          deliveryDisposition: "retry_scheduled",
          error: workerHandlerError,
          handlerStarted: true,
          ...contextEvidence,
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

      phase = "dead-letter";
      queue.deadLetter(entry, workerHandlerError);
      phase = "observation";
      recordWorkerObservation(metricDiagnostics, options, entry, profile, startedAt, {
        outcome: "failed",
        deliveryDisposition: "dead_lettered",
        error: workerHandlerError,
        handlerStarted: true,
        ...contextEvidence,
      });
      endWorkerTrace(profile, traceSpan, {
        outcome: "failed",
        deliveryDisposition: "dead_lettered",
        error: workerHandlerError,
        handlerStarted: true,
      });
      return { ok: true, value: deadLettered(entry, workerHandlerError, job.name) };
    }
    } catch (error) {
      if (!rawBoundaryReported) boundary(phase, "thrown", error);
      throw error;
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
          return workerFailure("PLATFORM_WORKER_NOT_READY", "Platform worker lifecycle failed to start.", {}, started.error, diagnosticDefinitions());
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
        diagnostics,
        lifecycleReady: lifecycle.isReady(),
        healthChecks: mounted.value.healthChecks,
        clock: options.deps.clock,
      }),
      shutdown: async () => {
        try { queue.close(); }
        catch (error) {
          reportWorkerBoundary(diagnostics, { operation: "shutdown", phase: "queue-close", boundary: "selection-or-invocation", effect: "lifecycle-shutdown-not-invoked" }, error, diagnosticDefinitions());
          throw error;
        }
        const shutdown = await lifecycle.shutdown();
        if (!shutdown.ok) {
          return workerFailure("PLATFORM_WORKER_NOT_READY", "Platform worker lifecycle failed to shut down.", {}, shutdown.error, diagnosticDefinitions());
        }

        return workerSuccess();
      },
    },
  };
}

function validateJobPayload(job: PlatformJobRegistration, message: QueueMessage, diagnosticDefinitions: () => readonly DiagnosticDefinition[], observe: (record: DiagnosticRecord, cause?: unknown) => void): PlatformWorkerError | undefined {
  if (job.validator === undefined || job.validator.validate(message.payload)) {
    return undefined;
  }

  const detail = validationDiagnostic(job.validator, message.payload);
  const own = captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ field: "payload", condition: "validator-rejected", effect: "handler-not-invoked" }));
  observe(own, detail === undefined ? undefined : { diagnosticRecord: detail });
  return workerError("PLATFORM_WORKER_INVALID_PAYLOAD", "Queue message payload failed job validation.", {
    jobName: String(job.name),
    messageType: String(message.type),
  }, detail === undefined ? undefined : { diagnosticRecord: detail }, diagnosticDefinitions(), own);
}

type WorkerBoundaryObserver = (phase: WorkerDeliveryBoundaryDetail["phase"], reason: WorkerDeliveryBoundaryDetail["reason"],
  cause?: unknown, effect?: WorkerDeliveryBoundaryDetail["effect"]) => DiagnosticRecord;

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
  diagnosticDefinitions: () => readonly DiagnosticDefinition[],
  boundary: WorkerBoundaryObserver,
  observe: (record: DiagnosticRecord, cause?: unknown) => void,
): Promise<Result<DurableOutboxClaim, PlatformWorkerError>> {
  const processing = options.durableOutboxProcessing;
  if (processing === undefined) {
    return { ok: true, value: { kind: "not-configured" } };
  }

  const identity = durableOutboxEntryId(message);
  if (!identity.ok) {
    return identity;
  }

  let phase: WorkerDeliveryBoundaryDetail["phase"] = "claim";
  try {
    const claim = await processing.processingStore.claim({
      outboxEntryId: identity.value,
      owner: processing.owner,
      acquiredAt: (phase = "claim-clock", isoDateTimeFromDate(options.deps.clock.now())),
      leaseDurationMs: (phase = "claim", processing.leaseDurationMs),
    });
    phase = "claim-result";
    if (!claim.ok) {
      const own = boundary("claim", "returned-failure", claim.error, "handler-not-invoked");
      return { ok: false, error: durableProcessingFailure("claim", claim.error, diagnosticDefinitions(), own) };
    }

    if (claim.value.disposition === "already-completed") {
      const outcome = claim.value.record.completion?.outcome;
      if (outcome === undefined) {
        const own = captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ field: "completion-outcome", condition: "absent", effect: "handler-not-invoked" }));
        observe(own);
        return {
          ok: false,
          error: workerError(
            "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
            "Completed durable outbox processing did not supply a completion outcome.",
            { phase: "claim" },
            undefined, [], own,
          ),
        };
      }
      return { ok: true, value: { kind: "already-completed", outboxEntryId: identity.value, outcome } };
    }

    if (claim.value.disposition === "lease-active") {
      const own = captureWorkerDiagnostic(() => workerCoordinationRecord("lease-active")); observe(own);
      return {
        ok: false,
        error: workerError(
          "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY",
          "Durable outbox processing is already claimed by another worker.",
          { phase: "claim" },
          undefined, [], own,
        ),
      };
    }

    const lease = claim.value.record.lease;
    if (lease === undefined) {
      const own = captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ field: "claimed-lease", condition: "absent", effect: "handler-not-invoked" })); observe(own);
      return {
        ok: false,
        error: workerError(
          "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
          "Durable outbox processing claim did not supply a lease.",
          { phase: "claim" },
          undefined, [], own,
        ),
      };
    }

    return { ok: true, value: { kind: "claimed", outboxEntryId: identity.value, fence: lease.fence } };
  } catch (error) {
    const own = boundary(phase, "thrown", error, "handler-not-invoked");
    return {
      ok: false,
      error: workerError(
        "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
        "Durable outbox processing claim failed.",
        { phase: "claim" },
        error,
        diagnosticDefinitions(),
        own,
      ),
    };
  }
}

function durableOutboxEntryId(message: QueueMessage): Result<OutboxEntryId, PlatformWorkerError> {
  const payload = message.payload;
  let record = false;
  let observedId: unknown;
  if (!(record = isRecord(payload)) || typeof (observedId = (payload as Readonly<Record<string, unknown>>).outboxEntryId) !== "string" || (observedId = (payload as Readonly<Record<string, unknown>>).outboxEntryId as string).length === 0) {
    return durableOutboxEnvelopeFailure(record ? "outbox-id" : "payload", !record ? payload === null ? "null" : Array.isArray(payload) ? "array" : "nonobject"
      : observedId === undefined ? "absent" : typeof observedId !== "string" ? "wrong-type" : "empty");
  }

  const outboxId = (payload as Readonly<Record<string, string>>).outboxEntryId!;
  let messageMatches = false;
  if (!(messageMatches = String(message.id) === outboxId) || String(message.idempotencyKey ?? "") !== outboxId) {
    return durableOutboxEnvelopeFailure(messageMatches ? "idempotency-key" : "message-id", "mismatch");
  }

  return { ok: true, value: outboxEntryId(outboxId) };
}

function durableOutboxEnvelopeFailure(field: "payload" | "outbox-id" | "message-id" | "idempotency-key", condition: "null" | "array" | "nonobject" | "absent" | "wrong-type" | "empty" | "mismatch"): Result<never, PlatformWorkerError> {
  return {
    ok: false,
    error: workerError(
      "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID",
      "Durable outbox delivery must preserve one stable outbox identity.",
      undefined, undefined, [], captureWorkerDiagnostic(() => workerDeliveryRejectedRecord({ field, condition, effect: "handler-not-invoked" })),
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
}, diagnosticDefinitions: () => readonly DiagnosticDefinition[], boundary: WorkerBoundaryObserver): Promise<Result<void, PlatformWorkerError>> {
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
      const own = boundary(input.terminal ? "terminal-complete" : "release", "returned-failure", settled.error, "settlement-unknown");
      return { ok: false, error: durableProcessingFailure(input.terminal ? "complete" : "release", settled.error, diagnosticDefinitions(), own) };
    }
    return { ok: true, value: undefined };
  } catch (error) {
    const own = boundary(input.terminal ? "terminal-complete" : "release", "thrown", error, "settlement-unknown");
    return {
      ok: false,
      error: workerError(
        "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
        "Durable outbox processing settlement failed.",
        { phase: input.terminal ? "complete" : "release" },
        error,
        diagnosticDefinitions(),
        own,
      ),
    };
  }
}

function durableProcessingFailure(
  phase: "claim" | "complete" | "release",
  error: { readonly code: string },
  diagnosticDefinitions: readonly DiagnosticDefinition[],
  fallback?: DiagnosticRecord,
): PlatformWorkerError {
  return workerError(
    "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED",
    "Durable outbox processing could not record its required state.",
    { phase, persistenceCode: error.code },
    error,
    diagnosticDefinitions,
    fallback,
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

  const profile = profilesByName.get(String(job.observability.profile));
  return profile === undefined ? undefined : { ...profile,
    errorClasses: Object.freeze([...new Set([...workerDiagnosticErrorCodes, ...(platformErrorClassDeclarations(profile) ?? [])])]) };
}

function recordWorkerObservationUnchecked(
  metricDiagnostics: PlatformMetricDiagnosticBinding,
  options: PlatformWorkerShellOptions,
  entry: PlatformWorkerQueueEntry,
  profile: PlatformCapabilityObservabilityProfile | undefined,
  startedAt: Date,
  event: PlatformWorkerObservabilityEvent,
  observations?: PlatformObservationDiagnostics,
): void {
  if (profile === undefined) {
    return;
  }

  const nomenclature = workerNomenclature(profile, event);
  if (platformProfileAllowsSignal(profile, "operational_log")) {
    if (event.error !== undefined && options.deps.diagnostics !== undefined) {
      // Retain the original correlation accessor evaluation here even when the same context failure was already observed before cleanup.
      const context: PlatformDiagnosticContext = { capability: "platform-worker", operation: "delivery", stage: "request",
        ...(entry.message.correlationId === undefined ? {} : { correlationId: entry.message.correlationId }) };
      if (!event.diagnosticAlreadyReported) reportPlatformErrorDiagnostic(options.deps.diagnostics, event.error, context);
    }
    writePlatformLog(options.deps.logger, {
      level: workerLogLevel(event),
      message: "platform.worker.job.delivery",
      fields: platformProfileLogFields(profile, nomenclature),
    }, profile, observations);
  }

  if (!platformProfileAllowsSignal(profile, "metric")) {
    return;
  }

  const labels = platformProfileMetricLabels(profile, nomenclature);
  const diagnosticBinding = platformProfileAllowsSignal(profile, "operational_log") ? metricDiagnostics : undefined;
  recordPlatformMetric(options.deps.metrics, options.deps.clock, {
    name: "platform.worker.job.delivery",
    labels,
  }, diagnosticBinding === undefined ? undefined : { binding: diagnosticBinding, operation: "job-delivery" }, observations);

  const finishedAt = options.deps.clock.now();
  if (event.handlerStarted && platformProfileMeasuresLatency(profile, "job_execution_latency")) {
    recordPlatformMetric(options.deps.metrics, options.deps.clock, {
      name: "platform.worker.job.execution_latency",
      kind: "timer",
      value: elapsedMilliseconds(startedAt, finishedAt),
      unit: "ms",
      labels,
    }, diagnosticBinding === undefined ? undefined : { binding: diagnosticBinding, operation: "job-execution" }, observations);
  }

  if (platformProfileMeasuresLatency(profile, "queue_wait_latency")) {
    recordPlatformMetric(options.deps.metrics, options.deps.clock, {
      name: "platform.worker.job.queue_wait_latency",
      kind: "timer",
      value: elapsedMilliseconds(new Date(entry.enqueuedAt), startedAt),
      unit: "ms",
      labels,
    }, diagnosticBinding === undefined ? undefined : { binding: diagnosticBinding, operation: "job-queue-wait" }, observations);
  }
}

function endWorkerTraceUnchecked(
  profile: PlatformCapabilityObservabilityProfile | undefined,
  span: TraceSpan | undefined,
  event: PlatformWorkerObservabilityEvent,
  observations?: PlatformObservationDiagnostics,
): void {
  if (profile === undefined || span === undefined) {
    return;
  }

  endPlatformTraceSpan(span, {
    outcome: event.outcome,
    attributes: platformProfileTraceFields(profile, workerNomenclature(profile, event)),
  }, profile, observations);
}

function startWorkerTrace(
  tracer: PlatformWorkerShellOptions["tracer"] | undefined,
  entry: PlatformWorkerQueueEntry,
  profile: PlatformCapabilityObservabilityProfile | undefined,
  observations?: PlatformObservationDiagnostics,
): TraceSpan | undefined {
  if (profile === undefined || !platformProfileAllowsSignal(profile, "trace")) {
    return undefined;
  }

  return startPlatformTraceSpan(tracer ?? noopTracer, {
    name: "platform.worker.job",
    ...(entry.message.traceParent === undefined ? {} : { parent: entry.message.traceParent }),
  }, profile, observations);
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
    ...(event.error === undefined ? {} : { errorClass: platformErrorClass(event.error, profile) }),
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
  readonly diagnosticAlreadyReported?: boolean;
  readonly outcome: TraceSpanOutcome;
  readonly deliveryDisposition?: PlatformJobDeliveryDisposition;
  readonly error?: PlatformWorkerError;
  readonly handlerStarted?: boolean;
}

function workerSuccess(): Result<void, PlatformWorkerError> {
  return { ok: true, value: undefined };
}
