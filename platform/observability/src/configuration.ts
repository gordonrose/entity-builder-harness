import { createConfigIssueCollector, type ConfigCheckFailure, type ConfigCheckIssue } from "@kanbien/core/config";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { Result } from "@kanbien/core/shared";
import { platformMetricDiagnosticDefinitions } from "./metric-diagnostics";
import { platformMetricLifecycleDiagnosticDefinitions } from "./metric-lifecycle-diagnostics";
import { platformReadinessDiagnosticDefinitions } from "./readiness-diagnostics";
import { platformObservationDiagnosticDefinitions } from "./boundary-definitions";

export const observabilityConfigurationReasons = [
  "missing", "wrong-type", "blank", "empty", "invalid-json", "wrong-shape", "invalid-format", "unsupported",
  "invalid-integer", "not-finite", "not-positive", "out-of-range", "duplicate", "required-for-kind", "forbidden-for-kind",
  "not-strictly-increasing", "malformed-url", "protocol-not-allowed", "port-not-allowed", "path-not-allowed",
  "credentials-not-allowed", "query-not-allowed", "fragment-not-allowed", "host-not-allowed", "boundary-mismatch",
  "interval-too-short", "timeout-exceeds-interval", "timeout-not-shorter-than-cadence", "stale-deadline-too-short",
] as const;
export type ObservabilityConfigurationReason = typeof observabilityConfigurationReasons[number];
export type ObservabilityConfigurationIssue = ConfigCheckIssue<ObservabilityConfigurationReason>;
export type ObservabilityConfigurationFailure = ConfigCheckFailure<ObservabilityConfigurationReason>;
export const observabilityConfigurationSettings = [
  "metrics.configuration", "metrics.provider", "metrics.endpoint", "metrics.delivery-boundary", "metrics.region", "metrics.service-name", "metrics.service-version",
  "metrics.deployment-environment", "metrics.export-interval", "metrics.export-timeout", "metrics.series", "series.source-name",
  "series.source-kind", "series.source-unit", "series.instrument-name", "series.description", "series.allowed-labels", "series.cardinality", "series.buckets",
  "readiness.configuration", "readiness.target", "readiness.scope", "readiness.workload", "readiness.dependency", "readiness.cadence", "readiness.timeout", "readiness.stale-after",
] as const;
export const observabilityConfigurationDiagnostic = defineDiagnostic({ code: "observability.configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["configuration-validation"] }, effect: { type: "enum", values: ["not-started"] },
    issues: { type: "array", minItems: 1, maxItems: 32, items: { type: "object", properties: {
      setting: { type: "enum", values: observabilityConfigurationSettings }, reason: { type: "enum", values: observabilityConfigurationReasons },
      index: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
      attributeIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
      relatedIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    }, optional: ["index", "attributeIndex", "relatedIndex"] } },
    truncated: { type: "boolean" },
  } },
} as const);
export const observabilityConstructionDiagnostic = defineDiagnostic({ code: "observability.runtime-construction-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { phase: { type: "enum", values: ["runtime-construction"] },
    reason: { type: "enum", values: ["unclassified-construction-failure"] }, effect: { type: "enum", values: ["not-assessed"] } } },
} as const);
export const platformObservabilityDiagnosticCatalog = { owner: "observability", definitions: [observabilityConfigurationDiagnostic, observabilityConstructionDiagnostic, ...platformMetricDiagnosticDefinitions, ...platformMetricLifecycleDiagnosticDefinitions, ...platformReadinessDiagnosticDefinitions, ...platformObservationDiagnosticDefinitions] } as const;
export function observabilityConfigurationRecord(failure: ObservabilityConfigurationFailure): DiagnosticRecord {
  try {
    if (!observabilityConfigurationObject(failure) || Reflect.ownKeys(failure).sort().join(",") !== "issues,truncated") throw new TypeError();
    const checked = createDiagnosticRecord<unknown>(observabilityConfigurationDiagnostic, { phase: "configuration-validation", effect: "not-started",
      issues: observabilityConfigurationField(failure, "issues"), truncated: observabilityConfigurationField(failure, "truncated") });
    if (checked.ok) return checked.value;
  } catch { /* Never retain submitted evidence or native exception text. */ }
  throw new TypeError("OBSERVABILITY_CONFIGURATION_DIAGNOSTIC_INVALID");
}
/** Merge only validator-produced failures; retain overflow from every child. */
export function mergeObservabilityConfigurationFailures(...failures: readonly ObservabilityConfigurationFailure[]): ObservabilityConfigurationFailure {
  const collector = createConfigIssueCollector<ObservabilityConfigurationReason>();
  for (const failure of failures) for (const issue of failure.issues) collector.add(issue);
  const checked = collector.finish();
  return { issues: checked.issues, truncated: checked.truncated || failures.some((failure) => failure.truncated) };
}
export function observabilityConstructionRecord(): DiagnosticRecord {
  const checked = createDiagnosticRecord(observabilityConstructionDiagnostic, { phase: "runtime-construction", reason: "unclassified-construction-failure", effect: "not-assessed" });
  if (!checked.ok) throw new TypeError("OBSERVABILITY_CONSTRUCTION_DIAGNOSTIC_INVALID");
  return checked.value;
}

/** Read only own data fields. Accessors, exotic objects and sparse arrays are not configuration data. */
export function observabilityConfigurationObject(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    && (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
}
export function observabilityConfigurationField(value: Readonly<Record<string, unknown>>, key: string): unknown {
  const field = Object.getOwnPropertyDescriptor(value, key);
  return !field ? undefined : "value" in field ? field.value : invalidDataField;
}
const invalidDataField = Symbol("invalid-configuration-data-field");
export function observabilityTextIssue(value: unknown): ObservabilityConfigurationReason | undefined {
  return value === undefined ? "missing" : typeof value !== "string" ? "wrong-type" : value.trim().length === 0 ? "blank" : undefined;
}
export function observabilityIntegerIssue(value: unknown): ObservabilityConfigurationReason | undefined {
  return value === undefined ? "missing" : typeof value !== "number" ? (typeof value === "string" && value.trim() === "" ? "blank" : "wrong-type")
    : Number.isNaN(value) || !Number.isInteger(value) && Number.isFinite(value) ? "invalid-integer"
    : !Number.isFinite(value) ? "not-finite" : value <= 0 ? "not-positive" : undefined;
}
export function observabilityArray(value: unknown): readonly unknown[] | undefined {
  if (!Array.isArray(value) || Object.getPrototypeOf(value) !== Array.prototype) return undefined;
  const length = Object.getOwnPropertyDescriptor(value, "length");
  if (!length || !("value" in length) || Reflect.ownKeys(value).length !== length.value + 1) return undefined;
  const snapshot: unknown[] = [];
  for (let i = 0; i < length.value; i++) { const field = Object.getOwnPropertyDescriptor(value, String(i)); if (!field || !("value" in field) || !field.enumerable) return undefined; snapshot.push(field.value); }
  return snapshot;
}

export interface PlatformReadinessConfiguration {
  readonly identity: { readonly target: string; readonly scope: string; readonly workload: string; readonly dependency: string };
  readonly cadenceMs: number; readonly timeoutMs: number; readonly staleAfterMs: number;
}
export function validatePlatformReadinessConfiguration(value: { readonly target: unknown; readonly scope: unknown; readonly workload: unknown; readonly dependency: unknown;
  readonly cadenceMs: unknown; readonly timeoutMs: unknown; readonly staleAfterMs: unknown }): Result<PlatformReadinessConfiguration, ObservabilityConfigurationFailure> {
  const collector = createConfigIssueCollector<ObservabilityConfigurationReason>();
  if (!observabilityConfigurationObject(value)) { collector.add({ setting: "readiness.configuration", reason: "wrong-shape" }); return { ok: false, error: collector.finish() }; }
  const fields = Object.fromEntries(["target", "scope", "workload", "dependency", "cadenceMs", "timeoutMs", "staleAfterMs"].map((key) => [key, observabilityConfigurationField(value, key)]));
  for (const key of ["target", "scope", "workload", "dependency"] as const) {
    const raw = fields[key]; const reason = observabilityTextIssue(raw) ?? (typeof raw === "string" && !/^[a-z][a-z0-9-]{1,63}$/.test(raw) ? "invalid-format" : undefined);
    if (reason) collector.add({ setting: `readiness.${key}`, reason });
  }
  const cadence = observabilityIntegerIssue(fields["cadenceMs"]), timeout = observabilityIntegerIssue(fields["timeoutMs"]), stale = observabilityIntegerIssue(fields["staleAfterMs"]);
  for (const [setting, reason] of [["readiness.cadence", cadence], ["readiness.timeout", timeout], ["readiness.stale-after", stale]] as const) if (reason) collector.add({ setting, reason });
  if (!cadence && !timeout && (fields["timeoutMs"] as number) >= (fields["cadenceMs"] as number)) collector.add({ setting: "readiness.timeout", reason: "timeout-not-shorter-than-cadence" });
  if (!cadence && !timeout && !stale && (fields["staleAfterMs"] as number) < (fields["cadenceMs"] as number) + (fields["timeoutMs"] as number)) collector.add({ setting: "readiness.stale-after", reason: "stale-deadline-too-short" });
  const failure = collector.finish(); if (failure.issues.length) return { ok: false, error: failure };
  return { ok: true, value: { identity: { target: fields["target"] as string, scope: fields["scope"] as string, workload: fields["workload"] as string, dependency: fields["dependency"] as string },
    cadenceMs: fields["cadenceMs"] as number, timeoutMs: fields["timeoutMs"] as number, staleAfterMs: fields["staleAfterMs"] as number } };
}
