import { defineDiagnostic } from "@kanbien/core/diagnostics";

/** Compatibility failures without a declared setting schema remain explicitly coarse. */
export const platformConfigDiagnostic = defineDiagnostic({ code: "platform-config.schema-rejected", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { schemaIndex: { type: "integer", minimum: 0, maximum: 65535 }, reason: { type: "enum", values: ["missing", "invalid"] } } },
} as const);
/** The v1 position bound remains immutable; larger existing schema lists need
 * a versioned position range rather than silently losing their observation.
 */
export const platformConfigWideDiagnostic = defineDiagnostic({ code: "platform-config.schema-rejected", version: 2,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { schemaIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER }, reason: { type: "enum", values: ["missing", "invalid"] } } },
} as const);
export const platformConfigThrownDiagnostic = defineDiagnostic({ code: "platform-config.schema-boundary-threw", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    schemaIndex: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    phase: { type: "enum", values: ["parse", "projection"] },
    reason: { type: "enum", values: ["boundary-threw"] },
    effect: { type: "enum", values: ["result-not-returned"] },
  } },
} as const);

export const platformConfigurationLoadingDiagnostic = defineDiagnostic({
  code: "platform-config.loading-declaration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["requirements", "bindings", "source", "assembly"] },
    reason: { type: "enum", values: ["wrong-type", "identity-count-mismatch", "missing", "invalid-format", "reserved"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);
export const platformConfigDiagnosticCatalog = { owner: "platform-config", definitions: [platformConfigDiagnostic, platformConfigWideDiagnostic, platformConfigThrownDiagnostic, platformConfigurationLoadingDiagnostic] } as const;
