import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

export const coreTenancyBoundaryDiagnostic = defineDiagnostic({
  code: "core.tenancy.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["tenant-context"] },
    phase: { type: "enum", values: ["input-projection", "result-projection"] },
    field: { type: "enum", values: ["tenant-id", "isolation-key"] },
    reason: { type: "enum", values: ["threw"] }, effect: { type: "enum", values: ["value-not-produced"] },
  } },
} as const);
export const coreTenancyDiagnosticDefinitions = Object.freeze([coreTenancyBoundaryDiagnostic]);
export type CoreTenancyBoundaryDetail = NonNullable<typeof coreTenancyBoundaryDiagnostic.__detail>;
export interface CoreTenancyDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreTenancyBoundaryDetail) => unknown;
}
export function coreTenancyBoundaryDiagnosticRecord(detail: CoreTenancyBoundaryDetail): DiagnosticRecord<CoreTenancyBoundaryDetail> {
  const record = createDiagnosticRecord(coreTenancyBoundaryDiagnostic, detail);
  if (!record.ok) throw new TypeError("CORE_TENANCY_DIAGNOSTIC_INVALID");
  return record.value;
}
