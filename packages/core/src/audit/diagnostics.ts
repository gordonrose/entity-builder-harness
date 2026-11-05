import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

export const coreAuditValidationDiagnostic = defineDiagnostic({ code: "core.audit.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["event-type", "event-version", "target"] },
    field: { type: "enum", values: ["type", "version", "target-type", "target-id"] },
    reason: { type: "enum", values: ["invalid-format", "not-integer", "not-positive", "empty", "untrimmed"] },
    effect: { type: "enum", values: ["rejected"] },
  } },
} as const);
export const coreAuditBoundaryDiagnostic = defineDiagnostic({ code: "core.audit.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["event-type", "event-version", "actor", "target", "event", "record", "recorded-events"] },
    phase: { type: "enum", values: ["predicate", "parameter-formatting", "input-projection", "actor-copy", "target-copy", "metadata-enumeration", "metadata-copy", "record-copy", "record-append", "snapshot-copy"] },
    field: { type: "enum", values: ["type", "version", "id", "outcome", "actor", "actor-type", "actor-id", "subject", "tenant-id", "occurred-at", "correlation-id", "target", "target-type", "target-id", "parent", "reason", "metadata"] },
    reason: { type: "enum", values: ["threw"] },
    effect: { type: "enum", values: ["result-not-returned", "append-not-reached", "append-outcome-unknown", "snapshot-not-returned"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["field", "ordinal"] },
} as const);
export const coreAuditDiagnosticDefinitions = Object.freeze([coreAuditValidationDiagnostic, coreAuditBoundaryDiagnostic]);
export type CoreAuditValidationDetail = NonNullable<typeof coreAuditValidationDiagnostic.__detail>;
export type CoreAuditBoundaryDetail = NonNullable<typeof coreAuditBoundaryDiagnostic.__detail>;
export interface CoreAuditDiagnosticContext {
  readonly operation: CoreAuditValidationDetail["operation"] | CoreAuditBoundaryDetail["operation"];
  readonly phase?: CoreAuditBoundaryDetail["phase"];
  readonly field?: CoreAuditBoundaryDetail["field"];
}
export interface CoreAuditDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreAuditDiagnosticContext) => unknown;
}
export interface CoreAuditErrorEvidence {
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly relatedDiagnosticDefinitions: readonly DiagnosticDefinition[];
}
export function coreAuditValidationDiagnosticRecord(detail: CoreAuditValidationDetail) { return required(coreAuditValidationDiagnostic, detail); }
export function coreAuditBoundaryDiagnosticRecord(detail: CoreAuditBoundaryDetail) { return required(coreAuditBoundaryDiagnostic, detail); }
function required<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const record = createDiagnosticRecord(definition, detail);
  if (!record.ok) throw new TypeError("CORE_AUDIT_DIAGNOSTIC_INVALID");
  return record.value;
}
