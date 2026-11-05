import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

export const coreMonitoringValidationDiagnostic = defineDiagnostic({
  code: "core.monitoring.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["identifier", "component", "health-result", "signal-definition", "metric-point", "metric-labels"] },
    field: { type: "enum", values: ["component-name", "component-type", "health-name", "health-type", "health-status", "signal-name", "signal-category", "signal-owner", "signal-intents", "signal-intent", "span-name", "trace-id", "span-id", "duration", "metric-kind", "metric-value", "max-string-length"] },
    reason: { type: "enum", values: ["empty", "untrimmed", "invalid-format", "closed-value-rejected", "not-finite", "negative"] },
    effect: { type: "enum", values: ["rejected"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["ordinal"] },
} as const);

export const coreMonitoringBoundaryDiagnostic = defineDiagnostic({
  code: "core.monitoring.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["identifier", "component", "health-result", "signal-definition", "metric-point", "metric-labels", "metadata", "fixed-health-check", "trace-context", "trace-start", "trace-end", "trace-snapshot"] },
    phase: { type: "enum", values: ["input-projection", "predicate-invocation", "component-copy", "metadata-enumeration", "metadata-copy", "intent-iteration", "result-copy", "label-options", "label-normalization", "label-enumeration", "label-copy", "parent-projection", "context-copy", "attribute-copy", "append", "return-context", "record-lookup", "end-projection", "record-replacement", "snapshot-copy"] },
    field: { type: "enum", values: ["component-name", "component-type", "health-name", "health-type", "health-status", "signal-name", "signal-category", "signal-owner", "signal-intents", "signal-intent", "span-name", "trace-id", "span-id", "duration", "metric-kind", "metric-value", "max-string-length", "name", "type", "status", "component", "checked-at", "message", "metadata", "additional-unsafe-label-names", "labels", "intents", "metric", "description", "unit", "recorded-at", "parent", "parent-trace-id", "parent-span-id", "attributes", "outcome", "context", "end"] },
    reason: { type: "enum", values: ["threw"] },
    effect: { type: "enum", values: ["result-not-returned", "sequence-advanced-record-not-added", "sequence-advanced-append-unknown", "record-added-span-not-returned", "end-marked-record-not-replaced", "end-marked-replacement-unknown", "snapshot-not-returned"] },
  }, optional: ["field"] },
} as const);
export const coreMonitoringDiagnosticDefinitions = Object.freeze([coreMonitoringValidationDiagnostic, coreMonitoringBoundaryDiagnostic]);
export type CoreMonitoringValidationDetail = NonNullable<typeof coreMonitoringValidationDiagnostic.__detail>;
export type CoreMonitoringBoundaryDetail = NonNullable<typeof coreMonitoringBoundaryDiagnostic.__detail>;
export interface CoreMonitoringDiagnosticContext {
  readonly operation: CoreMonitoringBoundaryDetail["operation"];
  readonly phase?: CoreMonitoringBoundaryDetail["phase"];
  readonly field?: CoreMonitoringBoundaryDetail["field"];
}
export interface CoreMonitoringDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreMonitoringDiagnosticContext) => unknown;
}
function required<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const result = createDiagnosticRecord(definition, detail);
  if (!result.ok) throw new TypeError("CORE_MONITORING_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreMonitoringValidationDiagnosticRecord(detail: CoreMonitoringValidationDetail) { return required(coreMonitoringValidationDiagnostic, detail); }
export function coreMonitoringBoundaryDiagnosticRecord(detail: CoreMonitoringBoundaryDetail) { return required(coreMonitoringBoundaryDiagnostic, detail); }
