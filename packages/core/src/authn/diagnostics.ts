import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

export const coreAuthnBoundaryDiagnostic = defineDiagnostic({
  code: "core.authn.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["principal"] },
    phase: { type: "enum", values: ["input-projection", "claims-enumeration", "claims-copy", "scopes-copy", "result-projection"] },
    field: { type: "enum", values: ["id", "type", "subject", "current-tenant-id", "claims", "scopes"] },
    reason: { type: "enum", values: ["threw"] },
    effect: { type: "enum", values: ["value-not-produced"] },
  } },
} as const);
export const coreAuthnDiagnosticDefinitions = Object.freeze([coreAuthnBoundaryDiagnostic]);
export type CoreAuthnBoundaryDetail = NonNullable<typeof coreAuthnBoundaryDiagnostic.__detail>;
export type CoreAuthnDiagnosticContext = CoreAuthnBoundaryDetail & { readonly evidence: "owned" | "source" };
export interface CoreAuthnDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreAuthnDiagnosticContext) => unknown;
}
export function coreAuthnBoundaryDiagnosticRecord(detail: CoreAuthnBoundaryDetail): DiagnosticRecord<CoreAuthnBoundaryDetail> {
  const record = createDiagnosticRecord(coreAuthnBoundaryDiagnostic, detail);
  if (!record.ok) throw new TypeError("CORE_AUTHN_DIAGNOSTIC_INVALID");
  return record.value;
}
