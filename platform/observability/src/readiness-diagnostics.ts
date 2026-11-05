import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";

const classification = { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" } as const;
export const readinessConfigurationDiagnostic = defineDiagnostic({ code: "observability.readiness-configuration-invalid", version: 1,
  classification: { ...classification, failureKind: "configuration", failureSource: "platform" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["timeout"] }, reason: { type: "enum", values: ["wrong-type", "not-finite", "not-integer", "not-positive"] },
    phase: { type: "enum", values: ["configuration"] }, effect: { type: "enum", values: ["probe-not-invoked"] },
  } },
} as const);
export const readinessNotReadyDiagnostic = defineDiagnostic({ code: "observability.readiness-probe-not-ready", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["result"] }, effect: { type: "enum", values: ["returned-not-ready"] },
  } },
} as const);
export const readinessInvocationDiagnostic = defineDiagnostic({ code: "observability.readiness-probe-threw", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["invocation"] }, effect: { type: "enum", values: ["unknown"] },
  } },
} as const);
export const readinessRejectionDiagnostic = defineDiagnostic({ code: "observability.readiness-probe-rejected", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["completion"] }, effect: { type: "enum", values: ["unknown"] },
  } },
} as const);
export const readinessDeadlineDiagnostic = defineDiagnostic({ code: "observability.readiness-probe-deadline-observed", version: 1, classification,
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["deadline"] }, effect: { type: "enum", values: ["unknown"] },
  } },
} as const);
export const platformReadinessDiagnosticDefinitions = [readinessConfigurationDiagnostic, readinessNotReadyDiagnostic,
  readinessInvocationDiagnostic, readinessRejectionDiagnostic, readinessDeadlineDiagnostic] as const;

export function readinessDiagnosticRecord(definition: DiagnosticDefinition, detail: unknown): DiagnosticRecord {
  const checked = createDiagnosticRecord<unknown>(definition, detail);
  if (!checked.ok) throw new TypeError("OBSERVABILITY_READINESS_DIAGNOSTIC_INVALID");
  return checked.value;
}
