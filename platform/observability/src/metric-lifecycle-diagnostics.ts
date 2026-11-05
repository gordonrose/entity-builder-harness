import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";

const classification = { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" } as const;
export const metricCollectionDiagnostic = defineDiagnostic({ code: "observability.metric-collection-issues", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["collection"] },
    reason: { type: "enum", values: ["errors-returned"] },
    effect: { type: "enum", values: ["collection-result-returned-completeness-unknown"] },
    errorCount: { type: "integer", minimum: 1, maximum: Number.MAX_SAFE_INTEGER },
  } },
} as const);
export const metricCollectionFailureDiagnostic = defineDiagnostic({ code: "observability.metric-collection-failed", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["collection"] }, reason: { type: "enum", values: ["rejected", "sdk-timeout"] },
    effect: { type: "enum", values: ["unknown"] },
  } },
} as const);
export const metricExportDiagnostic = defineDiagnostic({ code: "observability.metric-export-failed", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["export"] }, reason: { type: "enum", values: ["callback-failed", "invocation-threw"] },
    effect: { type: "enum", values: ["unknown"] },
  } },
} as const);
const lifecycleDetail = (phase: "flush" | "shutdown") => ({ type: "object", properties: {
  phase: { type: "enum", values: [phase] }, boundary: { type: "enum", values: ["exporter", "runtime"] },
  reason: { type: "enum", values: ["rejected", "sdk-timeout", "invocation-threw"] }, effect: { type: "enum", values: ["unknown"] },
} } as const);
export const metricFlushDiagnostic = defineDiagnostic({ code: "observability.metric-flush-failed", version: 1, classification, detail: lifecycleDetail("flush") });
export const metricShutdownDiagnostic = defineDiagnostic({ code: "observability.metric-shutdown-failed", version: 1, classification, detail: lifecycleDetail("shutdown") });
export const platformMetricLifecycleDiagnosticDefinitions = [metricCollectionDiagnostic, metricCollectionFailureDiagnostic, metricExportDiagnostic, metricFlushDiagnostic, metricShutdownDiagnostic] as const;

export function metricCollectionIssuesRecord(errorCount: number): DiagnosticRecord {
  return record(metricCollectionDiagnostic, { phase: "collection", reason: "errors-returned", effect: "collection-result-returned-completeness-unknown", errorCount });
}
export function metricCollectionFailureRecord(reason: "rejected" | "sdk-timeout"): DiagnosticRecord {
  return record(metricCollectionFailureDiagnostic, { phase: "collection", reason, effect: "unknown" });
}
export function metricExportFailureRecord(reason: "callback-failed" | "invocation-threw"): DiagnosticRecord {
  return record(metricExportDiagnostic, { phase: "export", reason, effect: "unknown" });
}
export function metricLifecycleFailureRecord(phase: "flush" | "shutdown", boundary: "exporter" | "runtime", reason: "rejected" | "sdk-timeout" | "invocation-threw"): DiagnosticRecord {
  return record(phase === "flush" ? metricFlushDiagnostic : metricShutdownDiagnostic, { phase, boundary, reason, effect: "unknown" });
}
function record(definition: DiagnosticDefinition, detail: unknown): DiagnosticRecord {
  const checked = createDiagnosticRecord<unknown>(definition, detail);
  if (!checked.ok) throw new TypeError("OBSERVABILITY_METRIC_LIFECYCLE_DIAGNOSTIC_INVALID");
  Object.freeze(checked.value.detail); return Object.freeze(checked.value);
}
