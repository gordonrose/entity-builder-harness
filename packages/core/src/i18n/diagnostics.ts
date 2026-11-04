import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

const validationOperations = ["locale-tag", "message-template", "translation-catalog", "translation-params", "interpolate"] as const;
const validationFields = ["locale", "template", "catalog-key", "parameter"] as const;
const ordinal = { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER } as const;

export const coreI18nValidationDiagnostic = defineDiagnostic({ code: "core.i18n.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: validationOperations },
    field: { type: "enum", values: validationFields },
    reason: { type: "enum", values: ["invalid-format", "empty", "contains-whitespace", "unsafe-name", "missing-own-property"] },
    effect: { type: "enum", values: ["predicate-rejected"] }, ordinal,
  }, optional: ["ordinal"] },
} as const);
export const coreI18nSelectionDiagnostic = defineDiagnostic({ code: "core.i18n.selection-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["translate"] },
    phase: { type: "enum", values: ["source-selection"] },
    selection: { type: "enum", values: ["requested-catalog", "fallback-catalog", "default-message"] },
    reason: { type: "enum", values: ["candidate-present", "no-message-key", "no-candidate-match", "default-translator"] },
    effect: { type: "enum", values: ["source-selected"] }, ordinal, catalogMisses: ordinal, templateMisses: ordinal,
  }, optional: ["ordinal", "catalogMisses", "templateMisses"] },
} as const);
export const coreI18nBoundaryDiagnostic = defineDiagnostic({ code: "core.i18n.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: [...validationOperations, "catalog-translator", "translate", "error"] },
    phase: { type: "enum", values: ["input-projection", "predicate-invocation", "normalization", "catalog-enumeration", "catalog-copy", "catalog-index", "candidate-iteration", "catalog-lookup", "template-lookup", "unsafe-name-declaration", "parameter-enumeration", "parameter-copy", "interpolation", "parameter-coercion", "result-projection", "error-projection"] },
    field: { type: "enum", values: [...validationFields, "catalogs", "catalog", "messages", "message", "request", "fallback-locales", "message-key", "default-message", "params", "additional-unsafe-param-names", "code", "cause", "diagnostic", "diagnostic-record", "details"] },
    reason: { type: "enum", values: ["threw"] }, effect: { type: "enum", values: ["value-not-produced"] }, ordinal,
  }, optional: ["field", "ordinal"] },
} as const);
export const coreI18nDiagnosticDefinitions = Object.freeze([coreI18nValidationDiagnostic, coreI18nSelectionDiagnostic, coreI18nBoundaryDiagnostic]);
export type CoreI18nValidationDetail = NonNullable<typeof coreI18nValidationDiagnostic.__detail>;
export type CoreI18nSelectionDetail = NonNullable<typeof coreI18nSelectionDiagnostic.__detail>;
export type CoreI18nBoundaryDetail = NonNullable<typeof coreI18nBoundaryDiagnostic.__detail>;
export interface CoreI18nDiagnosticContext {
  readonly operation: CoreI18nBoundaryDetail["operation"];
  readonly phase?: CoreI18nBoundaryDetail["phase"] | CoreI18nSelectionDetail["phase"];
  readonly field?: CoreI18nBoundaryDetail["field"];
}
export interface CoreI18nDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreI18nDiagnosticContext) => unknown;
}
export function coreI18nValidationDiagnosticRecord(detail: CoreI18nValidationDetail) { return required(coreI18nValidationDiagnostic, detail); }
export function coreI18nSelectionDiagnosticRecord(detail: CoreI18nSelectionDetail) { return required(coreI18nSelectionDiagnostic, detail); }
export function coreI18nBoundaryDiagnosticRecord(detail: CoreI18nBoundaryDetail) { return required(coreI18nBoundaryDiagnostic, detail); }
function required<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const record = createDiagnosticRecord(definition, detail);
  if (!record.ok) throw new TypeError("CORE_I18N_DIAGNOSTIC_INVALID");
  return record.value;
}
