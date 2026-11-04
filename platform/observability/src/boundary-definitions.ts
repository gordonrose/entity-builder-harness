import { defineDiagnostic } from "@kanbien/core/diagnostics";

export const platformObservationOperations = ["log-write", "trace-start", "trace-end", "trace-fields", "request-metric", "job-metric", "health-metric", "request-observation", "job-observation", "persistence-observation", "readiness-observation", "metric-runtime-construction", "metric-instrument-creation", "metric-recording", "metric-collection", "metric-export", "metric-flush", "metric-shutdown"] as const;
export const platformObservationBoundaryDiagnostic = defineDiagnostic({ code: "observability.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: platformObservationOperations },
    phase: { type: "enum", values: ["input-projection", "field-normalization", "error-class", "sink-selection", "sink-invocation", "sink-completion", "span-invocation", "span-validation", "span-end", "span-completion", "fallback", "clock", "elapsed-computation", "profile-projection", "metric-projection", "trace-projection", "log-projection", "result-projection", "identity-projection", "policy-selection", "event-validation", "event-output", "exporter-construction", "reader-construction", "provider-construction", "meter-selection", "port-construction", "runtime-construction", "instrument-creation", "instrument-recording", "collection", "export", "flush", "shutdown"] },
    reason: { type: "enum", values: ["threw", "rejected", "invalid-span", "invalid-event"] },
    effect: { type: "enum", values: ["not-attempted", "unknown", "no-op-returned", "fallback-threw", "observation-incomplete", "event-not-returned", "event-not-written", "input-rejected"] },
    field: { type: "enum", values: ["level", "message", "correlation-id", "fields", "error", "normalization-options", "name", "parent", "attributes", "outcome", "method", "route", "job", "status", "latency", "retry-count", "health-state", "error-class", "profile", "clock", "timestamp", "identity", "result", "policy", "event", "reporter", "logger", "record", "provider", "meter", "series", "endpoint", "aggregation-selector", "temporality-selector", "service-name", "service-version", "environment", "region", "export-interval", "export-timeout"] },
  }, optional: ["field"] },
} as const);
export type PlatformObservationBoundaryDetail = NonNullable<typeof platformObservationBoundaryDiagnostic.__detail>;
export const platformDiagnosticReportingSuppressedDiagnostic = defineDiagnostic({ code: "observability.diagnostic-reporting-suppressed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["attempt-limit"] }, limit: { type: "integer", minimum: 128, maximum: 128 },
    attempted: { type: "integer", minimum: 127, maximum: 127 }, effect: { type: "enum", values: ["further-observations-not-attempted"] },
  } },
} as const);
export const platformObservationDiagnosticDefinitions = [platformObservationBoundaryDiagnostic, platformDiagnosticReportingSuppressedDiagnostic] as const;
