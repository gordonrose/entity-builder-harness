import { createDiagnosticRecord, defineDiagnostic } from "../../../diagnostics/index";

const classification = { failureKind: "configuration", failureSource: "unknown", severity: "error", recovery: "manual_investigation" } as const;
export const coreConfigPrimitiveDiagnostic = defineDiagnostic({ code: "core.config.primitive-invalid", version: 1, classification,
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["environment-name", "secret-reference", "value"] },
    reader: { type: "enum", values: ["environment-name", "secret-reference", "required", "string", "number", "boolean"] },
    reason: { type: "enum", values: ["empty", "invalid-format", "missing", "wrong-type", "non-finite"] },
  } },
} as const);
export type CoreConfigReader = "required" | "optional" | "string" | "number" | "boolean" | "schema";
export const coreConfigSourceDiagnostic = defineDiagnostic({ code: "core.config.source-threw", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    reader: { type: "enum", values: ["required", "optional", "string", "number", "boolean", "schema"] },
    phase: { type: "enum", values: ["source-read"] }, reason: { type: "enum", values: ["invocation-threw"] },
    index: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["index"] },
} as const);
export const coreConfigDeclarationDiagnostic = defineDiagnostic({ code: "core.config.declaration-invalid", version: 1, classification,
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["definitions", "setting", "source", "minimum", "maximum", "bounds"] },
    reason: { type: "enum", values: ["empty", "too-many", "identity-count-mismatch", "invalid-format", "reserved", "not-safe-integer", "reversed", "predicate-rejected-unclassified"] },
    index: { type: "integer", minimum: 0, maximum: 31 },
  }, optional: ["index"] },
} as const);
export const coreConfigRelationshipDeclarationDiagnostic = defineDiagnostic({ code: "core.config.relationship-declaration-invalid", version: 1, classification,
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["relationships", "relationship", "rule", "left", "right", "participants"] },
    reason: { type: "enum", values: ["too-many", "identity-count-mismatch", "invalid-format", "unsupported", "undeclared", "self-reference", "duplicate-pair", "predicate-rejected-unclassified"] },
    index: { type: "integer", minimum: 0, maximum: 31 },
  }, optional: ["index"] },
} as const);
export const coreConfigChoiceDeclarationDiagnostic = defineDiagnostic({ code: "core.config.choice-declaration-invalid", version: 1, classification,
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["wrong-type", "empty", "too-many", "blank", "surrounding-whitespace", "duplicate"] },
    index: { type: "integer", minimum: 0, maximum: 31 },
  }, optional: ["index"] },
} as const);
export const coreConfigDiagnosticDefinitions = Object.freeze([
  coreConfigPrimitiveDiagnostic, coreConfigSourceDiagnostic, coreConfigDeclarationDiagnostic, coreConfigRelationshipDeclarationDiagnostic, coreConfigChoiceDeclarationDiagnostic,
]);
export const coreConfigDiagnosticCatalog = Object.freeze({ owner: "core.config", definitions: coreConfigDiagnosticDefinitions });
export function coreConfigPrimitiveRecord(detail: NonNullable<typeof coreConfigPrimitiveDiagnostic.__detail>) {
  const result = createDiagnosticRecord(coreConfigPrimitiveDiagnostic, detail);
  if (!result.ok) throw new TypeError("CORE_CONFIG_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreConfigSourceRecord(reader: CoreConfigReader, index?: number) {
  const result = createDiagnosticRecord(coreConfigSourceDiagnostic, { reader, phase: "source-read", reason: "invocation-threw", ...(index === undefined ? {} : { index }) });
  if (!result.ok) throw new TypeError("CORE_CONFIG_DIAGNOSTIC_INVALID");
  return result.value;
}
