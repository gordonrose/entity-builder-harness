import type { Result } from "@kanbien/core/shared";
import type { DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformOperationalEventDiagnosticRecord, type PlatformOperationalEventDiagnosticDetail } from "./registration-diagnostics";
import { observePlatformOperationalDiagnostic, PlatformOperationalObservation, type PlatformOperationalDiagnosticOptions } from "./operational-observations";

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
  readonly diagnosticRecord?: DiagnosticRecord;
}

/**
 * Validate the actual event boundary.  Reject unknown fields so a caller
 * cannot accidentally attach a provider response, nested error, secret, or
 * arbitrary fact to an otherwise well-formed readiness observation.
 */
export function platformReadinessObservationEvent(
  value: unknown,
  diagnostics?: PlatformOperationalDiagnosticOptions,
): Result<PlatformReadinessObservationEvent, PlatformOperationalEventError> {
  const observation = new PlatformOperationalObservation("readiness-event", "event-not-produced", diagnostics);
  let issue: EventIssue = { field: "event", condition: "predicate-rejected" };
  const failed = (detail: EventIssue): void => { issue = detail; };
  const reject = (field: EventIssue["field"], condition: EventIssue["condition"]): true => { failed({ field, condition }); return true; };
  const read = <T>(field: EventIssue["field"], action: () => T): T => observation.at("field-projection", field, action);
  return observation.run(() => {
  if (!isRecord(value, observation, failed) || !hasExactKeys(value, observation, failed)) return invalid(issue, diagnostics);
  if (read("type", () => value["type"]) !== "dependency.readiness-observed" && reject("type", "unsupported")) return invalid(issue, diagnostics);
  if (!boundedName(read("target", () => value["target"]), "target", observation, failed) || !boundedName(read("scope", () => value["scope"]), "scope", observation, failed) || !boundedName(read("workload", () => value["workload"]), "workload", observation, failed) || !boundedName(read("dependency", () => value["dependency"]), "dependency", observation, failed)) return invalid(issue, diagnostics);
  if (!isReadinessState(read("readiness", () => value["readiness"]), observation, failed) || !validIsoTime(read("observed-at", () => value["observedAt"]), observation, failed)) return invalid(issue, diagnostics);
  if (read("readiness", () => value["readiness"]) === "ready" && read("diagnostic-code", () => value["diagnosticCode"]) !== undefined && reject("diagnostic-code", "unexpected-present")) return invalid(issue, diagnostics);
  if (read("readiness", () => value["readiness"]) === "not-ready" && !isReadinessDiagnosticCode(read("diagnostic-code", () => value["diagnosticCode"]), observation, failed)) return invalid(issue, diagnostics);
  return {
    ok: true,
    value: {
      type: "dependency.readiness-observed",
      target: observation.at("result-projection", "target", () => value["target"]) as string,
      scope: observation.at("result-projection", "scope", () => value["scope"]) as string,
      workload: observation.at("result-projection", "workload", () => value["workload"]) as string,
      dependency: observation.at("result-projection", "dependency", () => value["dependency"]) as string,
      readiness: observation.at("result-projection", "readiness", () => value["readiness"]) as PlatformReadinessState,
      observedAt: observation.at("result-projection", "observed-at", () => value["observedAt"]) as string,
      ...(observation.at("result-projection", "diagnostic-code", () => value["diagnosticCode"]) === undefined ? {} : { diagnosticCode: observation.at("result-projection", "diagnostic-code", () => value["diagnosticCode"]) as string }),
    },
  };
  });
}

type EventIssue = Omit<PlatformOperationalEventDiagnosticDetail, "operation" | "phase" | "effect">;
type ObserveIssue = (issue: EventIssue) => void;
function isReadinessState(value: unknown, observation: PlatformOperationalObservation, failed: ObserveIssue): value is PlatformReadinessState {
  let condition: EventIssue["condition"] = "string-required";
  const valid = typeof value === "string" && (condition = "unsupported", observation.at("field-predicate", "readiness", () => (platformReadinessStates as readonly string[]).includes(value)));
  if (!valid) failed({ field: "readiness", condition });
  return valid;
}

function isReadinessDiagnosticCode(value: unknown, observation: PlatformOperationalObservation, failed: ObserveIssue): value is string {
  let condition: EventIssue["condition"] = "string-required";
  const valid = typeof value === "string" && (condition = "invalid-format", observation.at("field-predicate", "diagnostic-code", () => /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*){1,5}$/.test(value)));
  if (!valid) failed({ field: "diagnostic-code", condition });
  return valid;
}

function validIsoTime(value: unknown, observation: PlatformOperationalObservation, failed: ObserveIssue): value is string {
  let condition: EventIssue["condition"] = "string-required";
  const valid = typeof value === "string" && (condition = "invalid-format", observation.at("field-predicate", "observed-at", () => /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value))) && (condition = "date-parse-rejected", observation.at("time-parsing", "observed-at", () => !Number.isNaN(Date.parse(value))));
  if (!valid) failed({ field: "observed-at", condition });
  return valid;
}

function boundedName(value: unknown, field: EventIssue["field"], observation: PlatformOperationalObservation, failed: ObserveIssue): value is string {
  let condition: EventIssue["condition"] = "string-required";
  const valid = typeof value === "string" && (condition = "invalid-format", observation.at("field-predicate", field, () => /^[a-z][a-z0-9-]{1,63}$/.test(value)));
  if (!valid) failed({ field, condition });
  return valid;
}

function isRecord(value: unknown, observation: PlatformOperationalObservation, failed: ObserveIssue): value is Readonly<Record<string, unknown>> {
  let condition: EventIssue["condition"] = "object-required";
  const valid = typeof value === "object" && (condition = "null-rejected", value !== null) && (condition = "array-rejected", observation.at("structure", "event", () => !Array.isArray(value)));
  if (!valid) failed({ field: "event", condition });
  return valid;
}

function hasExactKeys(value: Readonly<Record<string, unknown>>, observation: PlatformOperationalObservation, failed: ObserveIssue): boolean {
  observation.location("key-enumeration", "keys");
  const allowed = new Set(["type", "target", "scope", "workload", "dependency", "readiness", "observedAt", "diagnosticCode"]);
  let first: EventIssue | undefined, visits = 0;
  const valid = keyTraversalSelection(Object.keys(value), observation).every((observation.location("key-traversal", "keys"), (key: string) => {
    const ordinal = visits++;
    const accepted = allowed.has(key);
    if (!accepted && first === undefined) first = { field: "keys", condition: "unknown-field", ...(ordinal <= 9007199254740991 ? { ordinal } : {}) };
    return accepted;
  }));
  if (!valid) failed(first ?? { field: "keys", condition: "predicate-rejected" });
  return valid;
}

function keyTraversalSelection(keys: string[], observation: PlatformOperationalObservation): string[] {
  observation.location("key-traversal-selection", "keys");
  return keys;
}

function invalid(issue: EventIssue, diagnostics?: PlatformOperationalDiagnosticOptions): Result<never, PlatformOperationalEventError> {
  const diagnosticRecord = platformOperationalEventDiagnosticRecord(issue);
  observePlatformOperationalDiagnostic(diagnostics, diagnosticRecord);
  return { ok: false, error: { code: "PLATFORM_OPERATIONAL_EVENT_INVALID", defaultMessage: "Operational event does not match the closed readiness observation envelope.", diagnosticRecord } };
}

