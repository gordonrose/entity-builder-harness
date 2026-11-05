import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";

const classification = { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" } as const;
const index = { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER } as const;
export const healthNotReadyDiagnostic = defineDiagnostic({ code: "health.check-not-ready", version: 1, classification,
  detail: { type: "object", properties: { index,
    status: { type: "enum", values: ["degraded", "unhealthy"] }, phase: { type: "enum", values: ["result"] },
    effect: { type: "enum", values: ["returned-not-ready"] },
  } },
} as const);
export const healthInvocationDiagnostic = defineDiagnostic({ code: "health.check-threw", version: 1, classification,
  detail: { type: "object", properties: { index, phase: { type: "enum", values: ["invocation"] }, effect: { type: "enum", values: ["unknown"] } } },
} as const);
export const healthRejectionDiagnostic = defineDiagnostic({ code: "health.check-rejected", version: 1, classification,
  detail: { type: "object", properties: { index, phase: { type: "enum", values: ["completion"] }, effect: { type: "enum", values: ["unknown"] } } },
} as const);
export const healthProjectionDiagnostic = defineDiagnostic({ code: "health.check-projection-failed", version: 1, classification,
  detail: { type: "object", properties: { index, phase: { type: "enum", values: ["projection"] }, effect: { type: "enum", values: ["output-unhealthy"] } } },
} as const);
export const healthLifecycleDiagnostic = defineDiagnostic({ code: "health.lifecycle-not-ready", version: 1, classification,
  detail: { type: "object", properties: { phase: { type: "enum", values: ["aggregation"] }, effect: { type: "enum", values: ["output-not-ready"] } } },
} as const);
export const platformHealthDiagnosticCatalog = { owner: "health", definitions: [healthNotReadyDiagnostic, healthInvocationDiagnostic, healthRejectionDiagnostic, healthProjectionDiagnostic, healthLifecycleDiagnostic] } as const;

export function healthDiagnosticRecord(definition: typeof platformHealthDiagnosticCatalog.definitions[number], detail: unknown): DiagnosticRecord {
  const checked = createDiagnosticRecord<unknown>(definition, detail);
  if (!checked.ok) throw new TypeError("PLATFORM_HEALTH_DIAGNOSTIC_INVALID");
  return checked.value;
}
