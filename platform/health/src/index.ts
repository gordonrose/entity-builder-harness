import {
  type HealthCheckResult,
  type HealthStatus,
} from "@kanbien/core/monitoring";
import {
  isoDateTimeFromDate,
  type Clock,
  type ISODateTime,
} from "@kanbien/core/shared";
import type { PlatformDiagnosticReporter, PlatformHealthRegistration } from "@kanbien/platform-contracts";
import { reportPlatformDiagnostic, reportPlatformErrorDiagnostic } from "@kanbien/platform-observability";
import { healthDiagnosticRecord, healthNotReadyDiagnostic, healthInvocationDiagnostic, healthRejectionDiagnostic, healthProjectionDiagnostic, healthLifecycleDiagnostic } from "./diagnostics";
import { publicHealthMessage, publicHealthMetadata, type PlatformPublicHealthMessage, type PlatformPublicHealthMetadata } from "./public-details";
export type { PlatformPublicHealthMessage, PlatformPublicHealthMetadata } from "./public-details";

export { platformHealthDiagnosticCatalog } from "./diagnostics";
const intrinsicPromiseThen = Promise.prototype.then;

export type PlatformHealthState = "live" | "ready" | "not-ready";

export interface PlatformLivenessSummary {
  readonly status: "live";
  readonly checkedAt: ISODateTime;
}

export interface PlatformReadinessSummary {
  readonly status: "ready" | "not-ready";
  readonly checkedAt: ISODateTime;
  readonly checks: readonly PlatformSafeHealthCheckResult[];
}

export interface PlatformSafeHealthCheckResult {
  readonly name: string;
  readonly type: HealthCheckResult["type"];
  readonly component: string;
  readonly status: HealthStatus;
  readonly checkedAt: ISODateTime;
  readonly durationMs?: number;
  readonly message?: PlatformPublicHealthMessage;
  readonly metadata?: PlatformPublicHealthMetadata;
}

export interface PlatformReadinessInput {
  readonly diagnostics?: PlatformDiagnosticReporter;
  readonly lifecycleReady: boolean;
  readonly healthChecks: readonly PlatformHealthRegistration[];
  readonly clock: Clock;
}

export function platformLiveness(clock: Clock): PlatformLivenessSummary {
  return {
    status: "live",
    checkedAt: isoDateTimeFromDate(clock.now()),
  };
}

export async function platformReadiness(
  input: PlatformReadinessInput,
): Promise<PlatformReadinessSummary> {
  const checkedAt = isoDateTimeFromDate(input.clock.now());
  const checks = await Promise.all(input.healthChecks.map((registration, index) => runSafeHealthCheck(registration, checkedAt, index, input.diagnostics)));
  const checksReady = checks.every((check) => check.status === "healthy");
  if (!input.lifecycleReady && input.diagnostics !== undefined) {
    reportPlatformDiagnostic(input.diagnostics, healthDiagnosticRecord(healthLifecycleDiagnostic, { phase: "aggregation", effect: "output-not-ready" }),
      { capability: "health", operation: "aggregate", stage: "readiness" });
  }

  return {
    status: input.lifecycleReady && checksReady ? "ready" : "not-ready",
    checkedAt,
    checks,
  };
}

export function platformHealthHttpStatus(status: PlatformHealthState): number {
  return status === "not-ready" ? 503 : 200;
}

async function runSafeHealthCheck(
  registration: PlatformHealthRegistration,
  checkedAt: ISODateTime,
  index: number,
  diagnostics: PlatformDiagnosticReporter | undefined,
): Promise<PlatformSafeHealthCheckResult> {
  let phase: "invocation" | "completion" | "projection" = "invocation";
  let evidence: unknown;
  const context = { capability: "health", operation: "check", stage: "readiness" } as const;
  try {
    const pending = registration.check.check();
    phase = "completion";
    // The check contract also permits synchronous values. Native promises are
    // observed with the intrinsic so a shadowed then cannot orphan rejection.
    const result = await new Promise<HealthCheckResult>((resolve, reject) => {
      try { Reflect.apply(intrinsicPromiseThen, pending, [resolve, reject]); }
      catch { Reflect.apply(intrinsicPromiseThen, Promise.resolve(pending), [resolve, reject]); }
    });
    evidence = result;
    phase = "projection";
    const safe = safeHealthCheckResult(result);
    if (diagnostics !== undefined && (safe.status === "degraded" || safe.status === "unhealthy")) {
      reportPlatformErrorDiagnostic(diagnostics, result, context);
      reportPlatformDiagnostic(diagnostics, healthDiagnosticRecord(healthNotReadyDiagnostic,
        { index, status: safe.status, phase: "result", effect: "returned-not-ready" }), context);
    }
    return safe;
  } catch (error) {
    if (diagnostics !== undefined) {
      if (phase === "projection") reportPlatformErrorDiagnostic(diagnostics, evidence, context);
      const definition = phase === "invocation" ? healthInvocationDiagnostic : phase === "completion" ? healthRejectionDiagnostic : healthProjectionDiagnostic;
      reportPlatformDiagnostic(diagnostics, healthDiagnosticRecord(definition,
        { index, phase, effect: phase === "projection" ? "output-unhealthy" : "unknown" }), context);
      reportPlatformErrorDiagnostic(diagnostics, error, context);
    }
    return {
      name: String(registration.name),
      type: "readiness",
      component: "runtime",
      status: "unhealthy",
      checkedAt,
      message: "Health check failed.",
      metadata: { failure: "check-failed" },
    };
  }
}

function safeHealthCheckResult(result: HealthCheckResult): PlatformSafeHealthCheckResult {
  const projected = {
    name: String(result.name),
    type: result.type,
    component: String(result.component.name),
    status: result.status,
    checkedAt: result.checkedAt,
    ...(result.durationMs === undefined ? {} : { durationMs: result.durationMs }),
  };
  return {
    ...projected,
    ...(result.message === undefined ? {} : { message: publicHealthMessage(projected.status) }),
    ...(result.metadata === undefined ? {} : { metadata: publicHealthMetadata(result.metadata) }),
  };
}
