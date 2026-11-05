import type { Logger } from "@kanbien/core/logging";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import type { Metrics } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate, type Clock } from "@kanbien/core/shared";
import {
  platformReadinessObservationEvent,
  type PlatformReadinessObservationEvent,
  type PlatformReadinessState,
} from "@kanbien/platform-contracts";
import { recordPlatformMetric } from "./metrics";
import { reportPlatformDiagnostic, reportPlatformErrorDiagnostic } from "./diagnostics";
import { createPlatformMetricDiagnosticBinding } from "./metric-diagnostics";
import { readinessConfigurationDiagnostic, readinessNotReadyDiagnostic, readinessInvocationDiagnostic,
  readinessRejectionDiagnostic, readinessDeadlineDiagnostic, readinessDiagnosticRecord } from "./readiness-diagnostics";
import { reportPlatformObservationBoundary, reportPlatformObservationSources, type PlatformObservationDiagnostics } from "./boundary-observation";
import type { PlatformObservationBoundaryDetail } from "./boundary-definitions";
import { observePlatformSinkCompletion } from "./diagnostics";

const intrinsicPromiseThen = Promise.prototype.then;

export interface PlatformReadinessProbeResult {
  readonly readiness: PlatformReadinessState;
  readonly diagnosticCode?: string;
  readonly diagnosticRecord?: DiagnosticRecord;
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
}

export interface PlatformReadinessObserverIdentity {
  readonly target: string;
  readonly scope: string;
  readonly workload: string;
  readonly dependency: string;
}

export interface PlatformReadinessObserverOptions {
  readonly observations?: PlatformObservationDiagnostics;
  readonly diagnostics?: PlatformDiagnosticReporter;
  readonly identity: PlatformReadinessObserverIdentity;
  readonly probe: () => Promise<PlatformReadinessProbeResult>;
  readonly logger: Logger;
  readonly metrics: Metrics;
  readonly clock: Clock;
  readonly timeoutMs: number;
  /** Capability-owned codes declared by the composed workload, not a platform registry. */
  readonly allowedDiagnosticCodes: readonly string[];
  readonly defaultDiagnosticCode: string;
}

export interface PlatformReadinessObserver {
  observe(): Promise<PlatformReadinessObservationEvent>;
}

/**
 * Observe an application dependency outside request handling.  Its caller
 * owns cadence and staleness policy; this primitive owns only the bounded
 * probe deadline, closed event emission, and application readiness metric.
 */
export function createPlatformReadinessObserver(options: PlatformReadinessObserverOptions): PlatformReadinessObserver {
  const metricDiagnostics = createPlatformMetricDiagnosticBinding(options.diagnostics, { capability: "observability", stage: "readiness" });
  return {
    observe: async () => {
      let observations: PlatformObservationDiagnostics | undefined;
      try { observations = options.observations; } catch { /* Optional selection cannot change the probe. */ }
      let phase: PlatformObservationBoundaryDetail["phase"] = "input-projection";
      let field: PlatformObservationBoundaryDetail["field"] = "result";
      let invalidEvent = false;
      let probeEvidence: unknown;
      const invalid = (): void => { invalidEvent = true; };
      try {
      field = "provider";
      const observation = await boundedProbe(options.probe, (field = "policy", options.timeoutMs));
      probeEvidence = observation.evidence;
      phase = "result-projection"; field = "result";
      const result = observation.result;
      // Retain the existing invalid-policy rejection. A configured fallback is
      // policy validation, never evidence that this dependency had that failure.
      let candidate: string | undefined;
      const selection = result.readiness === "ready" ? undefined : (candidate = result.diagnosticCode, phase = "policy-selection", field = "policy", allowedDiagnosticCode(options, candidate));
      let stamp: Date;
      const projected = {
        type: "dependency.readiness-observed",
        ...(phase = "identity-projection", field = "identity", options.identity),
        readiness: (phase = "result-projection", field = "result", result.readiness),
        observedAt: (phase = "clock", field = "clock", stamp = options.clock.now(), phase = "event-validation", field = "timestamp", isoDateTimeFromDate(stamp)),
        ...(selection === undefined ? {} : { diagnosticCode: selection.code }),
      };
      phase = "event-validation"; field = "event";
      const policyEvent = requiredReadinessEvent(projected, observations, invalid);
      const event = selection !== undefined && !selection.approvedCandidate
        ? requiredReadinessEvent({ ...policyEvent, diagnosticCode: observation.diagnostic.code }, observations, invalid) : policyEvent;
      phase = "input-projection"; field = "logger";
      const logger = options.logger;
      phase = "event-output";
      emitPlatformReadinessObservation(logger, event, observations);
      phase = "result-projection"; field = "result";
      if (result.readiness !== "ready") {
        if (options.diagnostics !== undefined) {
          const context = { capability: "observability", operation: "probe", stage: "readiness" } as const;
          reportPlatformDiagnostic(options.diagnostics, observation.diagnostic, context);
          reportPlatformErrorDiagnostic(options.diagnostics, observation.evidence, context);
        }
      }
      phase = "metric-projection";
      recordPlatformMetric(options.metrics, options.clock, {
        name: "platform.dependency.readiness",
        kind: "gauge",
        value: event.readiness === "ready" ? 1 : 0,
        unit: "count",
        labels: {
          target: event.target,
          scope: event.scope,
          workload: event.workload,
          dependency: event.dependency,
          readiness: event.readiness,
        },
      }, { binding: metricDiagnostics, operation: "readiness" }, observations);
      return event;
      } catch (error) {
        if (!invalidEvent && phase !== "event-output") reportPlatformObservationBoundary(observations, { operation: "readiness-observation", phase, field, reason: "threw", effect: "event-not-returned" }, error);
        // A later wrapper failure cannot erase evidence already returned by the
        // probe. Select the captured value without rereading or replaying it.
        reportPlatformObservationSources(observations, probeEvidence);
        throw error;
      }
    },
  };
}

/** Writes only the exact, validated envelope to the logger port. */
export function emitPlatformReadinessObservation(logger: Logger, event: PlatformReadinessObservationEvent, observations?: PlatformObservationDiagnostics): void {
  let checked: ReturnType<typeof platformReadinessObservationEvent>;
  try { checked = checkedReadinessEvent(event, observations); }
  catch (error) { reportPlatformObservationBoundary(observations, { operation: "readiness-observation", phase: "event-validation", field: "event", reason: "threw", effect: "event-not-written" }, error); throw error; }
  if (!checked.ok) { reportPlatformObservationBoundary(observations, { operation: "readiness-observation", phase: "event-validation", field: "event", reason: "invalid-event", effect: "event-not-written" }, checked.error); return; }
  let phase: PlatformObservationBoundaryDetail["phase"] = "sink-selection";
  let prepared: Parameters<Logger["write"]>[0];
  try {
    const pending: unknown = logger.write((prepared = {
      level: checked.value.readiness === "ready" ? "info" : "warn",
      message: "platform.dependency.readiness_observed",
      fields: {
        event_type: checked.value.type,
        target: checked.value.target,
        scope: checked.value.scope,
        workload: checked.value.workload,
        dependency: checked.value.dependency,
        readiness: checked.value.readiness,
        observed_at: checked.value.observedAt,
        ...(checked.value.diagnosticCode === undefined ? {} : { diagnostic_code: checked.value.diagnosticCode }),
      },
    }, phase = "sink-invocation", prepared));
    observePlatformSinkCompletion(pending, (error) => reportPlatformObservationBoundary(observations, { operation: "readiness-observation", phase: "sink-completion", field: "logger", reason: "rejected", effect: "unknown" }, error));
  } catch (error) {
    reportPlatformObservationBoundary(observations, { operation: "readiness-observation", phase, field: "logger", reason: "threw", effect: phase === "sink-selection" ? "event-not-written" : "unknown" }, error);
    // Observability delivery must not alter application readiness or business work.
  }
}

async function boundedProbe(
  probe: () => Promise<PlatformReadinessProbeResult>,
  timeoutMs: number,
): Promise<ProbeObservation> {
  const invalidTimeout = typeof timeoutMs !== "number" ? "wrong-type" : !Number.isFinite(timeoutMs) ? "not-finite"
    : !Number.isInteger(timeoutMs) ? "not-integer" : timeoutMs <= 0 ? "not-positive" : undefined;
  if (invalidTimeout !== undefined) {
    return { result: { readiness: "not-ready" }, diagnostic: readinessDiagnosticRecord(readinessConfigurationDiagnostic,
      { field: "timeout", reason: invalidTimeout, phase: "configuration", effect: "probe-not-invoked" }) };
  }
  let timer: ReturnType<typeof setTimeout> | undefined;
  let pending: Promise<PlatformReadinessProbeResult>;
  try { pending = probe(); }
  catch (error) {
    return { result: { readiness: "not-ready" }, evidence: error,
      diagnostic: readinessDiagnosticRecord(readinessInvocationDiagnostic, { phase: "invocation", effect: "unknown" }) };
  }
  try {
    const notReady = readinessDiagnosticRecord(readinessNotReadyDiagnostic, { phase: "result", effect: "returned-not-ready" });
    const completed = new Promise<ProbeObservation>((resolve, reject) => {
      const fulfilled = (result: PlatformReadinessProbeResult): void => resolve({ result, evidence: result, diagnostic: notReady });
      try { Reflect.apply(intrinsicPromiseThen, pending, [fulfilled, reject]); }
      catch { Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [fulfilled, reject]); }
    });
    return await Promise.race([
      completed,
      new Promise<ProbeObservation>((resolve) => {
        timer = setTimeout(() => resolve({ result: { readiness: "not-ready" },
          diagnostic: readinessDiagnosticRecord(readinessDeadlineDiagnostic, { phase: "deadline", effect: "unknown" }) }), timeoutMs);
      }),
    ]);
  } catch (error) {
    return { result: { readiness: "not-ready" }, evidence: error,
      diagnostic: readinessDiagnosticRecord(readinessRejectionDiagnostic, { phase: "completion", effect: "unknown" }) };
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

interface ProbeObservation {
  readonly result: PlatformReadinessProbeResult;
  readonly diagnostic: DiagnosticRecord;
  readonly evidence?: unknown;
}

function requiredReadinessEvent(value: unknown, observations?: PlatformObservationDiagnostics, rejected?: () => void): PlatformReadinessObservationEvent {
  const checked = checkedReadinessEvent(value, observations);
  if (!checked.ok) {
    rejected?.();
    reportPlatformObservationBoundary(observations, { operation: "readiness-observation", phase: "event-validation", field: "event", reason: "invalid-event", effect: "event-not-returned" }, checked.error);
    throw new Error(checked.error.code);
  }
  return checked.value;
}

/** Keep the parser-owned raw location separate from its unchanged wrapper/source9. */
function checkedReadinessEvent(value: unknown, observations?: PlatformObservationDiagnostics): ReturnType<typeof platformReadinessObservationEvent> {
  let owned: DiagnosticRecord | undefined;
  try {
    return platformReadinessObservationEvent(value, observations === undefined ? undefined : {
      onDiagnostic(record, context) { if (context.evidence === "owned") owned = record; },
    });
  } catch (error) {
    if (owned !== undefined) reportPlatformObservationSources(observations, { diagnosticRecord: owned });
    throw error;
  }
}

function allowedDiagnosticCode(options: PlatformReadinessObserverOptions, candidate: string | undefined): { readonly code: string; readonly approvedCandidate: boolean } {
  if (typeof candidate === "string" && options.allowedDiagnosticCodes.includes(candidate)) return { code: candidate, approvedCandidate: true };
  if (options.allowedDiagnosticCodes.includes(options.defaultDiagnosticCode)) return { code: options.defaultDiagnosticCode, approvedCandidate: false };
  throw new Error("PLATFORM_READINESS_OBSERVATION_DIAGNOSTIC_POLICY_INVALID");
}

