import { captureDiagnosticRecord, requireDiagnosticRecord, diagnosticProcessingDefinition, createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { metricValidationReasons, type Metrics } from "@kanbien/core/monitoring";
import type { PlatformDiagnosticContext, PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { platformMetricLifecycleDiagnosticDefinitions } from "./metric-lifecycle-diagnostics";
import { reportPlatformDiagnostic } from "./diagnostics";
import { platformDiagnosticReportingSuppressedDiagnostic } from "./boundary-definitions";

const classification = { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" } as const;
export const metricPreparationDiagnostic = defineDiagnostic({ code: "observability.metric-preparation-failed", version: 1, classification,
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["name", "kind", "value", "unit", "label", "clock", "timestamp", "recorder"] },
    reason: { type: "enum", values: [...metricValidationReasons, "wrong-type", "access-failed", "clock-threw", "invalid-date", "unclassified-preparation-failure"] },
    phase: { type: "enum", values: ["point-preparation"] }, effect: { type: "enum", values: ["recording-not-attempted"] },
    index: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["index"] },
} as const);
export const metricRejectionReasons = ["undeclared-metric", "kind-mismatch", "unit-mismatch", "not-finite", "negative-counter", "negative-distribution", "unapproved-label"] as const;
export const metricRejectionDiagnostic = defineDiagnostic({ code: "observability.metric-rejected", version: 1, classification,
  detail: { type: "object", properties: {
    reason: { type: "enum", values: metricRejectionReasons }, phase: { type: "enum", values: ["point-validation"] },
    effect: { type: "enum", values: ["recording-not-attempted"] },
    seriesIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    index: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["seriesIndex", "index"] },
} as const);
export const metricCreationDiagnostic = defineDiagnostic({ code: "observability.metric-instrument-creation-failed", version: 1, classification,
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["unclassified-creation-failure"] }, phase: { type: "enum", values: ["instrument-creation"] },
    effect: { type: "enum", values: ["recording-not-attempted"] }, seriesIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  } },
} as const);
export const metricRecordingDiagnostic = defineDiagnostic({ code: "observability.metric-recording-failed", version: 1, classification,
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["unclassified-invocation-failure"] }, phase: { type: "enum", values: ["record-invocation"] },
    effect: { type: "enum", values: ["unknown"] }, seriesIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["seriesIndex"] },
} as const);
export const platformMetricDiagnosticDefinitions = [metricPreparationDiagnostic, metricRejectionDiagnostic, metricCreationDiagnostic, metricRecordingDiagnostic] as const;

/** Protect required producer evidence without changing a metric's result or retrying it. */
export function capturePlatformMetricDiagnostic(build: () => DiagnosticRecord): DiagnosticRecord {
  return requireDiagnosticRecord([...platformMetricDiagnosticDefinitions, ...platformMetricLifecycleDiagnosticDefinitions], captureDiagnosticRecord(build));
}

export function metricPreparationRecord(field: "name" | "kind" | "value" | "unit" | "label" | "clock" | "timestamp" | "recorder",
  reason: typeof metricValidationReasons[number] | "wrong-type" | "access-failed" | "clock-threw" | "invalid-date" | "unclassified-preparation-failure", index?: number): DiagnosticRecord {
  return requiredRecord(metricPreparationDiagnostic, { field, reason, phase: "point-preparation", effect: "recording-not-attempted", ...(index === undefined ? {} : { index }) });
}
export function metricRejectionRecord(reason: typeof metricRejectionReasons[number], seriesIndex?: number, index?: number): DiagnosticRecord {
  return requiredRecord(metricRejectionDiagnostic, { reason, phase: "point-validation", effect: "recording-not-attempted",
    ...(seriesIndex === undefined ? {} : { seriesIndex }), ...(index === undefined ? {} : { index }) });
}
export function metricCreationRecord(seriesIndex: number): DiagnosticRecord {
  return requiredRecord(metricCreationDiagnostic, { reason: "unclassified-creation-failure", phase: "instrument-creation", effect: "recording-not-attempted", seriesIndex });
}
export function metricRecordingRecord(seriesIndex?: number): DiagnosticRecord {
  return requiredRecord(metricRecordingDiagnostic, { reason: "unclassified-invocation-failure", phase: "record-invocation", effect: "unknown", ...(seriesIndex === undefined ? {} : { seriesIndex }) });
}
function requiredRecord(definition: typeof platformMetricDiagnosticDefinitions[number], detail: unknown): DiagnosticRecord {
  const checked = createDiagnosticRecord<unknown>(definition, detail);
  if (!checked.ok) throw new TypeError("OBSERVABILITY_METRIC_DIAGNOSTIC_INVALID");
  Object.freeze(checked.value.detail);
  return Object.freeze(checked.value);
}

// Only the same thrown object and same emitting port can supply classified evidence.
// Merely copying a valid diagnosticRecord (or wrapping a different port) proves nothing.
const origins = new WeakMap<object, { readonly port: Metrics; readonly record: DiagnosticRecord }>();
export function attachPlatformMetricDiagnostic(port: Metrics, error: Error, record: DiagnosticRecord): Error {
  const definition = metricDefinitionFor(record, [...platformMetricDiagnosticDefinitions, diagnosticProcessingDefinition()]);
  if (!definition) throw new TypeError("OBSERVABILITY_METRIC_DIAGNOSTIC_INVALID");
  const checked = parseDiagnosticRecord<unknown>(definition, record);
  if (!checked.ok) throw new TypeError("OBSERVABILITY_METRIC_DIAGNOSTIC_INVALID");
  Object.freeze(checked.value.detail); Object.freeze(checked.value);
  Object.defineProperty(error, "diagnosticRecord", { value: checked.value, enumerable: true });
  origins.set(error, { port, record: checked.value });
  return error;
}
export function platformMetricFailureObservation(port: Metrics, error: unknown): DiagnosticRecord | undefined {
  if (typeof error !== "object" || error === null) return undefined;
  const observation = origins.get(error);
  return observation?.port === port ? observation.record : undefined;
}

/** Lookup only own data descriptors; malformed public input cannot run getters. */
function metricDefinitionFor(record: unknown, definitions: readonly DiagnosticDefinition[] = platformMetricDiagnosticDefinitions): DiagnosticDefinition | undefined {
  try {
    if (typeof record !== "object" || record === null) return undefined;
    const code = Object.getOwnPropertyDescriptor(record, "code"), version = Object.getOwnPropertyDescriptor(record, "definitionVersion");
    if (!code || !("value" in code) || !version || !("value" in version)) return undefined;
    return definitions.find((item) => item.code === code.value && item.version === version.value);
  } catch { return undefined; }
}

export const platformMetricOperations = ["metric", "request", "request-outcome", "request-latency", "health", "job", "job-delivery", "job-execution", "job-queue-wait", "persistence-transition", "readiness"] as const;
export type PlatformMetricOperation = typeof platformMetricOperations[number];
export interface PlatformMetricDiagnosticBinding { report(record: DiagnosticRecord, operation: PlatformMetricOperation): void }
export interface PlatformMetricDiagnosticOptions { readonly binding: PlatformMetricDiagnosticBinding; readonly operation: PlatformMetricOperation }
export const platformMetricDiagnosticLimit = 128;

/** One binding per shell/observer: finite lifetime budget, first observation per predicate/location.
 * No timers, arbitrary input keys, metric recursion, retries, or implied delivery guarantee.
 */
export function createPlatformMetricDiagnosticBinding(reporter: PlatformDiagnosticReporter | undefined,
  context: Omit<PlatformDiagnosticContext, "operation" | "correlationId">): PlatformMetricDiagnosticBinding {
  return boundedBinding(reporter, platformMetricDiagnosticDefinitions, platformMetricOperations, (operation) => ({ ...context, operation }));
}

export type PlatformMetricLifecycleOperation = "collection" | "export" | "flush" | "shutdown";
export interface PlatformMetricLifecycleDiagnosticBinding { report(record: DiagnosticRecord, operation: PlatformMetricLifecycleOperation): void }
/** Target/process-owned background reporting, independent from route profile signals. */
export function createPlatformMetricLifecycleDiagnosticBinding(reporter: PlatformDiagnosticReporter | undefined,
  context: Pick<PlatformDiagnosticContext, "capability">): PlatformMetricLifecycleDiagnosticBinding {
  return boundedBinding(reporter, platformMetricLifecycleDiagnosticDefinitions, ["collection", "export", "flush", "shutdown"],
    (operation) => ({ ...context, operation, stage: operation === "shutdown" ? "shutdown" : "runtime" }));
}

function boundedBinding<Operation extends string>(reporter: PlatformDiagnosticReporter | undefined,
  definitions: readonly DiagnosticDefinition[], operations: readonly Operation[],
  context: (operation: Operation) => PlatformDiagnosticContext): { report(record: DiagnosticRecord, operation: Operation): void } {
  const reported = new Set<string>();
  let reporting = false;
  let exhausted = false;
  return { report(record, operation) {
    if (reporter === undefined || reporting || exhausted) return;
    try {
      const definition = metricDefinitionFor(record, [...definitions, diagnosticProcessingDefinition()]);
      if (!definition || !operations.includes(operation)) return;
      const checked = parseDiagnosticRecord<unknown>(definition, record);
      if (!checked.ok) return;
      const key = `${operation}:${checked.value.code}:${JSON.stringify(checked.value.detail)}`;
      if (reported.has(key)) return;
      if (reported.size === platformMetricDiagnosticLimit - 1) {
        exhausted = true; reporting = true;
        const control = requireDiagnosticRecord([platformDiagnosticReportingSuppressedDiagnostic], captureDiagnosticRecord(() => {
          const result = createDiagnosticRecord(platformDiagnosticReportingSuppressedDiagnostic, { reason: "attempt-limit", limit: 128, attempted: 127, effect: "further-observations-not-attempted" });
          return result.ok ? result.value : undefined;
        }));
        reportPlatformDiagnostic(reporter, control, context(operation));
        return;
      }
      reported.add(key);
      reporting = true;
      reportPlatformDiagnostic(reporter, checked.value, context(operation));
    } catch { /* Reporting cannot change work or replay a measurement. */ }
    finally { reporting = false; }
  } };
}
