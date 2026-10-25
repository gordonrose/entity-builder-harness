import type { Result } from "@kanbien/core/shared";

/**
 * A deliberately small event vocabulary for operational observations.  This
 * is not a second diagnostic registry: capability owners still select the
 * diagnostic meaning.  It only owns the fixed envelope shared by emitted
 * readiness observations.
 */
export const platformOperationalEventTypes = ["dependency.readiness-observed"] as const;
export type PlatformOperationalEventType = (typeof platformOperationalEventTypes)[number];

export const platformReadinessStates = ["ready", "not-ready"] as const;
export type PlatformReadinessState = (typeof platformReadinessStates)[number];

/** These are semantic, provider-neutral classifications, never raw errors. */
export interface PlatformReadinessObservationEvent {
  readonly type: "dependency.readiness-observed";
  readonly target: string;
  readonly scope: string;
  readonly workload: string;
  readonly dependency: string;
  readonly readiness: PlatformReadinessState;
  readonly observedAt: string;
  /** Capability-owned stable classification, never a provider error/message. */
  readonly diagnosticCode?: string;
}

export interface PlatformOperationalEventError {
  readonly code: "PLATFORM_OPERATIONAL_EVENT_INVALID";
  readonly defaultMessage: string;
}

/**
 * Validate the actual event boundary.  Reject unknown fields so a caller
 * cannot accidentally attach a provider response, nested error, secret, or
 * arbitrary fact to an otherwise well-formed readiness observation.
 */
export function platformReadinessObservationEvent(
  value: unknown,
): Result<PlatformReadinessObservationEvent, PlatformOperationalEventError> {
  if (!isRecord(value) || !hasExactKeys(value)) return invalid();
  if (value["type"] !== "dependency.readiness-observed") return invalid();
  if (!boundedName(value["target"]) || !boundedName(value["scope"]) || !boundedName(value["workload"]) || !boundedName(value["dependency"])) return invalid();
  if (!isReadinessState(value["readiness"]) || !validIsoTime(value["observedAt"])) return invalid();
  if (value["readiness"] === "ready" && value["diagnosticCode"] !== undefined) return invalid();
  if (value["readiness"] === "not-ready" && !isReadinessDiagnosticCode(value["diagnosticCode"])) return invalid();
  return {
    ok: true,
    value: {
      type: "dependency.readiness-observed",
      target: value["target"],
      scope: value["scope"],
      workload: value["workload"],
      dependency: value["dependency"],
      readiness: value["readiness"],
      observedAt: value["observedAt"],
      ...(value["diagnosticCode"] === undefined ? {} : { diagnosticCode: value["diagnosticCode"] as string }),
    },
  };
}

function isReadinessState(value: unknown): value is PlatformReadinessState {
  return typeof value === "string" && (platformReadinessStates as readonly string[]).includes(value);
}

function isReadinessDiagnosticCode(value: unknown): value is string {
  return typeof value === "string" && /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*){1,5}$/.test(value);
}

function validIsoTime(value: unknown): value is string {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value) && !Number.isNaN(Date.parse(value));
}

function boundedName(value: unknown): value is string {
  return typeof value === "string" && /^[a-z][a-z0-9-]{1,63}$/.test(value);
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(value: Readonly<Record<string, unknown>>): boolean {
  const allowed = new Set(["type", "target", "scope", "workload", "dependency", "readiness", "observedAt", "diagnosticCode"]);
  return Object.keys(value).every((key) => allowed.has(key));
}

function invalid(): Result<never, PlatformOperationalEventError> {
  return { ok: false, error: { code: "PLATFORM_OPERATIONAL_EVENT_INVALID", defaultMessage: "Operational event does not match the closed readiness observation envelope." } };
}

