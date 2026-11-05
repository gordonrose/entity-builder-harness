import { createDiagnosticRecord, defineDiagnostic } from "../diagnostics/index";

export const corePermissionDiagnostic = defineDiagnostic({ code: "core.authz.permission-invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["resource", "action"] },
    reason: { type: "enum", values: ["empty", "surrounding-whitespace", "colon-separator", "whitespace"] },
  } },
} as const);
export const coreAuthzDiagnosticDefinitions = Object.freeze([corePermissionDiagnostic]);
export function corePermissionRecord(field: "resource" | "action", reason: NonNullable<typeof corePermissionDiagnostic.__detail>["reason"]) {
  const result = createDiagnosticRecord(corePermissionDiagnostic, { field, reason });
  if (!result.ok) throw new TypeError("CORE_PERMISSION_DIAGNOSTIC_INVALID");
  return result.value;
}
