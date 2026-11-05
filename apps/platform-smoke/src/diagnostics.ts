import { createDiagnosticRecord, defineDiagnostic } from "@kanbien/core/diagnostics";

/** Business meaning belongs here; no provider code, identifier or submitted value. */
export const platformSmokeAcceptanceDiagnostic = defineDiagnostic({ code: "platform-smoke.work-item-not-accepted", version: 1,
  classification: { failureKind: "unknown", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["accept-work-item"] },
    reason: { type: "enum", values: ["duplicate", "operation-failed"] },
    effect: { type: "enum", values: ["rejected", "unknown"] },
  } },
} as const);
export const platformSmokeAttributeDiagnostic = defineDiagnostic({ code: "platform-smoke.attribute-invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "app", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["payload", "payload.rebuild"] },
    reason: { type: "enum", values: ["unexpected-body", "missing", "wrong-type"] },
  } },
} as const);
export const platformSmokeConfigDiagnostic = defineDiagnostic({ code: "platform-smoke.configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "app", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { field: { type: "enum", values: ["app-name"] }, reason: { type: "enum", values: ["missing", "wrong-type"] } } },
} as const);
export const platformSmokeAcceptedPayloadDiagnostic = defineDiagnostic({ code: "platform-smoke.accepted-payload-invalid", version: 1,
  classification: { failureKind: "validation", failureSource: "app", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: { field: { type: "enum", values: ["payload", "payload.outboxEntryId"] }, reason: { type: "enum", values: ["wrong-shape", "missing", "wrong-type", "empty"] } } },
} as const);
export const platformSmokeAcceptedProjectionDiagnostic = defineDiagnostic({ code: "platform-smoke.accepted-payload-not-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: { field: { type: "enum", values: ["payload.outboxEntryId"] }, phase: { type: "enum", values: ["diagnostic-projection"] },
    reason: { type: "enum", values: ["accessor-not-read", "inspection-threw", "prototype-limit"] }, effect: { type: "enum", values: ["not-assessed"] } } },
} as const);
export const platformSmokeDiagnosticCatalog = { owner: "platform-smoke", definitions: [platformSmokeAcceptanceDiagnostic, platformSmokeAttributeDiagnostic,
  platformSmokeConfigDiagnostic, platformSmokeAcceptedPayloadDiagnostic, platformSmokeAcceptedProjectionDiagnostic] } as const;

export function platformSmokeConfigurationFailure(reason: "missing" | "wrong-type") {
  const checked = createDiagnosticRecord(platformSmokeConfigDiagnostic, { field: "app-name", reason });
  if (!checked.ok) throw new TypeError("PLATFORM_SMOKE_DIAGNOSTIC_INVALID");
  return checked.value;
}

/** Inspect data descriptors, not a second potentially stateful property getter.
 * Inherited data remains accepted exactly as in the legacy validator.
 */
export function platformSmokeAcceptedPayloadFailure(value: unknown) {
  const unavailable = (reason: "accessor-not-read" | "inspection-threw" | "prototype-limit") => {
    const checked = createDiagnosticRecord(platformSmokeAcceptedProjectionDiagnostic, { field: "payload.outboxEntryId", phase: "diagnostic-projection", reason, effect: "not-assessed" });
    if (!checked.ok) throw new TypeError("PLATFORM_SMOKE_DIAGNOSTIC_INVALID");
    return checked.value;
  };
  const invalid = (field: "payload" | "payload.outboxEntryId", reason: "wrong-shape" | "missing" | "wrong-type" | "empty") => {
    const checked = createDiagnosticRecord(platformSmokeAcceptedPayloadDiagnostic, { field, reason });
    if (!checked.ok) throw new TypeError("PLATFORM_SMOKE_DIAGNOSTIC_INVALID");
    return checked.value;
  };
  if (typeof value !== "object" || value === null) return invalid("payload", "wrong-shape");
  try {
    let current: object | null = value;
    for (let depth = 0; current !== null && depth < 32; depth++) {
      const field = Object.getOwnPropertyDescriptor(current, "outboxEntryId");
      if (field !== undefined) {
        if (!("value" in field)) return unavailable("accessor-not-read");
        const observed: unknown = field.value;
        return typeof observed !== "string" ? invalid("payload.outboxEntryId", "wrong-type")
          : observed.length === 0 ? invalid("payload.outboxEntryId", "empty") : undefined;
      }
      current = Object.getPrototypeOf(current) as object | null;
    }
    return current === null ? invalid("payload.outboxEntryId", "missing") : unavailable("prototype-limit");
  } catch { return unavailable("inspection-threw"); }
}

export function platformSmokeAttributeFailure(field: "payload" | "payload.rebuild", reason: "unexpected-body" | "missing" | "wrong-type") {
  const result = createDiagnosticRecord(platformSmokeAttributeDiagnostic, { field, reason });
  if (!result.ok) throw new TypeError("PLATFORM_SMOKE_DIAGNOSTIC_INVALID");
  return result.value;
}

export function platformSmokeAcceptanceFailure(code: string) {
  const duplicate = code === "PERSISTENCE_DUPLICATE";
  const result = createDiagnosticRecord(platformSmokeAcceptanceDiagnostic, {
    operation: "accept-work-item", reason: duplicate ? "duplicate" : "operation-failed", effect: duplicate ? "rejected" : "unknown",
  });
  if (!result.ok) throw new TypeError("PLATFORM_SMOKE_DIAGNOSTIC_INVALID");
  return result.value;
}
