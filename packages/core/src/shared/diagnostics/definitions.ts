import { defineDiagnostic } from "../../diagnostics/index";

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
export const coreUuidDiagnostic = defineDiagnostic({ code: "core.shared.uuid-invalid", version: 1, classification,
  detail: { type: "object", properties: { reason: { type: "enum", values: ["invalid-format"] } } },
} as const);
export const coreUuidGenerationDiagnostic = defineDiagnostic({ code: "core.shared.uuid-generation-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "error", recovery: "automation_retryable" },
  detail: { type: "object", properties: { reason: { type: "enum", values: ["generation-threw", "generated-value-invalid"] } } },
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
export const coreSharedDiagnosticDefinitions = Object.freeze([coreDateDiagnostic, coreDateNormalizationDiagnostic,
  coreUuidDiagnostic, coreUuidGenerationDiagnostic, coreJsonDiagnostic]);
