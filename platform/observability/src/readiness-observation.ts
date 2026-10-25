import type { Logger } from "@kanbien/core/logging";
import type { Metrics } from "@kanbien/core/monitoring";
import { isoDateTimeFromDate, type Clock } from "@kanbien/core/shared";
import {
  platformReadinessObservationEvent,
  type PlatformReadinessObservationEvent,
  type PlatformReadinessState,
} from "@kanbien/platform-contracts";
import { recordPlatformMetric } from "./metrics";

export interface PlatformReadinessProbeResult {
  readonly readiness: PlatformReadinessState;
  readonly diagnosticCode?: string;
}

export interface PlatformReadinessObserverIdentity {
  readonly target: string;
  readonly scope: string;
  readonly workload: string;
  readonly dependency: string;
}

export interface PlatformReadinessObserverOptions {
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
  return {
    observe: async () => {
      const result = await boundedProbe(options.probe, options.timeoutMs);
      const event = requiredReadinessEvent({
        type: "dependency.readiness-observed",
        ...options.identity,
        readiness: result.readiness,
        observedAt: isoDateTimeFromDate(options.clock.now()),
        ...(result.readiness === "ready" ? {} : { diagnosticCode: allowedDiagnosticCode(options, result.diagnosticCode) }),
      });
      emitPlatformReadinessObservation(options.logger, event);
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
      });
      return event;
    },
  };
}

/** Writes only the exact, validated envelope to the logger port. */
export function emitPlatformReadinessObservation(logger: Logger, event: PlatformReadinessObservationEvent): void {
  const checked = platformReadinessObservationEvent(event);
  if (!checked.ok) return;
  try {
    logger.write({
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
    });
  } catch {
    // Observability delivery must not alter application readiness or business work.
  }
}

async function boundedProbe(
  probe: () => Promise<PlatformReadinessProbeResult>,
  timeoutMs: number,
): Promise<PlatformReadinessProbeResult> {
  if (!Number.isInteger(timeoutMs) || timeoutMs <= 0) {
    return { readiness: "not-ready" };
  }
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      probe(),
      new Promise<PlatformReadinessProbeResult>((resolve) => {
        timer = setTimeout(() => resolve({ readiness: "not-ready" }), timeoutMs);
      }),
    ]);
  } catch {
    return { readiness: "not-ready" };
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

function requiredReadinessEvent(value: unknown): PlatformReadinessObservationEvent {
  const checked = platformReadinessObservationEvent(value);
  if (!checked.ok) throw new Error(checked.error.code);
  return checked.value;
}

function allowedDiagnosticCode(options: PlatformReadinessObserverOptions, candidate: string | undefined): string {
  if (typeof candidate === "string" && options.allowedDiagnosticCodes.includes(candidate)) return candidate;
  if (options.allowedDiagnosticCodes.includes(options.defaultDiagnosticCode)) return options.defaultDiagnosticCode;
  throw new Error("PLATFORM_READINESS_OBSERVATION_DIAGNOSTIC_POLICY_INVALID");
}

