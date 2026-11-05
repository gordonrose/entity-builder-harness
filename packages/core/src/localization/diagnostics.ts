import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

const validationOperations = ["currency-code", "region-code", "time-zone-id", "number", "currency"] as const;
const validationFields = ["currency", "region", "time-zone", "value", "amount", "minimum-fraction-digits", "maximum-fraction-digits", "fraction-range"] as const;
export const coreLocalizationValidationDiagnostic = defineDiagnostic({
  code: "core.localization.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: validationOperations },
    field: { type: "enum", values: validationFields },
    reason: { type: "enum", values: ["invalid-format", "parent-sequence-rejected", "not-finite", "not-integer", "negative", "minimum-exceeds-maximum"] },
    effect: { type: "enum", values: ["predicate-rejected"] },
  } },
} as const);
export const coreLocalizationUnsupportedDiagnostic = defineDiagnostic({
  code: "core.localization.unsupported-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["format"] },
    phase: { type: "enum", values: ["implementation-selection"] },
    reason: { type: "enum", values: ["unsupported-implementation"] },
    effect: { type: "enum", values: ["format-not-performed"] },
  } },
} as const);
export const coreLocalizationBoundaryDiagnostic = defineDiagnostic({
  code: "core.localization.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: [...validationOperations, "date-time", "region", "localized-format", "format", "error"] },
    phase: { type: "enum", values: ["input-projection", "predicate-invocation", "normalization", "parameter-formatting", "result-projection", "reason-projection", "error-projection"] },
    field: { type: "enum", values: [...validationFields, "locale", "kind", "text", "date-style", "time-style", "reason", "code", "default-message", "message-key", "params", "cause", "diagnostic", "diagnostic-record", "details"] },
    reason: { type: "enum", values: ["threw"] },
    effect: { type: "enum", values: ["value-not-produced"] },
  }, optional: ["field"] },
} as const);
export const coreLocalizationDiagnosticDefinitions = Object.freeze([coreLocalizationValidationDiagnostic, coreLocalizationUnsupportedDiagnostic, coreLocalizationBoundaryDiagnostic]);
export type CoreLocalizationValidationDetail = NonNullable<typeof coreLocalizationValidationDiagnostic.__detail>;
export type CoreLocalizationUnsupportedDetail = NonNullable<typeof coreLocalizationUnsupportedDiagnostic.__detail>;
export type CoreLocalizationBoundaryDetail = NonNullable<typeof coreLocalizationBoundaryDiagnostic.__detail>;
export interface CoreLocalizationDiagnosticContext {
  readonly operation: CoreLocalizationBoundaryDetail["operation"];
  readonly phase?: CoreLocalizationBoundaryDetail["phase"] | CoreLocalizationUnsupportedDetail["phase"];
  readonly field?: CoreLocalizationBoundaryDetail["field"];
}
export interface CoreLocalizationDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreLocalizationDiagnosticContext) => unknown;
}
function required<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const result = createDiagnosticRecord(definition, detail);
  if (!result.ok) throw new TypeError("CORE_LOCALIZATION_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreLocalizationValidationDiagnosticRecord(detail: CoreLocalizationValidationDetail) { return required(coreLocalizationValidationDiagnostic, detail); }
export function coreLocalizationUnsupportedDiagnosticRecord(detail: CoreLocalizationUnsupportedDetail) { return required(coreLocalizationUnsupportedDiagnostic, detail); }
export function coreLocalizationBoundaryDiagnosticRecord(detail: CoreLocalizationBoundaryDetail) { return required(coreLocalizationBoundaryDiagnostic, detail); }
