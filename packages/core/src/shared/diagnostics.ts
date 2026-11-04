import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "../diagnostics/index";

const classification = { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" } as const;
export const coreDateDiagnostic = defineDiagnostic({ code: "core.shared.date-invalid", version: 1, classification,
  detail: { type: "object", properties: { reason: { type: "enum", values: ["invalid-format", "parse-rejected"] } } },
} as const);
export const coreDateNormalizationDiagnostic = defineDiagnostic({ code: "core.shared.date-normalization-threw", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    phase: { type: "enum", values: ["string-normalization", "date-normalization"] }, reason: { type: "enum", values: ["invocation-threw"] },
  } },
} as const);
export const coreJsonDiagnostic = defineDiagnostic({ code: "core.shared.json-invalid", version: 1, classification,
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["non-finite-number", "non-plain-object"] },
    depth: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    path: { type: "array", minItems: 0, maxItems: 16, items: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER } },
    pathTruncated: { type: "boolean" },
    locationUnavailable: { type: "boolean" },
  }, optional: ["locationUnavailable"] },
} as const);
export const coreSharedDiagnosticDefinitions = Object.freeze([coreDateDiagnostic, coreDateNormalizationDiagnostic, coreJsonDiagnostic]);

/** Never replace an existing record or change a thrown value to make it writable. */
export function attachCoreDiagnosticRecord<T>(error: T, record: DiagnosticRecord): T {
  if ((typeof error === "object" && error !== null) || typeof error === "function") {
    try {
      if (!Object.getOwnPropertyDescriptor(error, "diagnosticRecord")) Object.defineProperty(error, "diagnosticRecord", { value: record, enumerable: true, configurable: true });
    } catch { /* Primitive, frozen and host errors may not retain evidence. */ }
  }
  return error;
}
export function coreDateRecord(reason: "invalid-format" | "parse-rejected") {
  const result = createDiagnosticRecord(coreDateDiagnostic, { reason });
  if (!result.ok) throw new TypeError("CORE_DATE_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreDateNormalizationRecord(phase: "string-normalization" | "date-normalization") {
  const result = createDiagnosticRecord(coreDateNormalizationDiagnostic, { phase, reason: "invocation-threw" });
  if (!result.ok) throw new TypeError("CORE_DATE_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreJsonRecord(reason: "non-finite-number" | "non-plain-object", depth: number, path: readonly number[], locationUnavailable = false) {
  const result = createDiagnosticRecord(coreJsonDiagnostic, { reason, depth, path, pathTruncated: depth > path.length,
    ...(locationUnavailable ? { locationUnavailable: true } : {}),
  });
  if (!result.ok) throw new TypeError("CORE_JSON_DIAGNOSTIC_INVALID");
  return result.value;
}
