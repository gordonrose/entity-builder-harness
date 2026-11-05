import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
export const coreLoggingBoundaryDiagnostic = defineDiagnostic({ code: "core.logging.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["log-record", "redact-fields", "create-redactor", "redact", "write"] },
    phase: { type: "enum", values: ["input-projection", "key-projection", "key-normalization", "key-iteration", "field-enumeration", "value-inspection", "value-traversal", "field-assignment", "record-projection", "redactor-selection", "redactor-invocation", "inner-selection", "inner-invocation"] },
    field: { type: "enum", values: ["level", "message", "correlation-id", "fields", "redaction-keys", "replacement", "redactor", "logger"] },
    reason: { type: "enum", values: ["threw", "rejected"] },
    effect: { type: "enum", values: ["result-not-returned", "inner-not-invoked", "inner-outcome-unknown"] },
  }, optional: ["field"] },
} as const);
export const coreLoggingDiagnosticDefinitions = Object.freeze([coreLoggingBoundaryDiagnostic]);
export type CoreLoggingBoundaryDetail = NonNullable<typeof coreLoggingBoundaryDiagnostic.__detail>;
export interface CoreLoggingDiagnosticContext {
  readonly operation: CoreLoggingBoundaryDetail["operation"];
  readonly phase: CoreLoggingBoundaryDetail["phase"];
  readonly field?: CoreLoggingBoundaryDetail["field"];
}
export interface CoreLoggingDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreLoggingDiagnosticContext) => unknown;
}
export function coreLoggingBoundaryDiagnosticRecord(detail: CoreLoggingBoundaryDetail) {
  const record = createDiagnosticRecord(coreLoggingBoundaryDiagnostic, detail);
  if (!record.ok) throw new TypeError("CORE_LOGGING_DIAGNOSTIC_INVALID");
  return record.value;
}
