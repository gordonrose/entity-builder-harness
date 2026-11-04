import {
  catalogMessageTranslator,
  defaultMessageTranslator,
  i18nError,
  localeTag,
  messageTemplate,
  safeTranslationParams,
  translationCatalog,
  interpolateMessageTemplate,
  coreI18nDiagnosticDefinitions,
  coreI18nValidationDiagnosticRecord,
  coreI18nSelectionDiagnosticRecord,
  coreI18nBoundaryDiagnosticRecord,
  type CoreI18nDiagnosticOptions,
  type CoreI18nDiagnosticContext,
  type CoreI18nValidationDetail,
  type CoreI18nSelectionDetail,
  type CoreI18nBoundaryDetail,
  type I18nError,
  type I18nErrorCode,
  type LocaleTag,
  type MessageTemplate,
  type MessageTranslator,
  type TranslationParamOptions,
  type TranslatedMessage,
  type TranslationCatalog,
  type TranslationRequest,
} from "../src/i18n/index";
import { isOk, messageDescriptor, type Result } from "../src/shared/index";

const localeResult = localeTag("en-GB");
if (!isOk(localeResult)) {
  throw new Error("Expected locale tag to be valid.");
}
const locale: LocaleTag = localeResult.value;

const templateResult = messageTemplate("Hello {name}");
if (!isOk(templateResult)) {
  throw new Error("Expected template to be valid.");
}
const template: MessageTemplate = templateResult.value;

const catalogResult: Result<TranslationCatalog, I18nError> = translationCatalog({
  locale,
  messages: {
    "greeting.hello": template,
  },
});
if (!isOk(catalogResult)) {
  throw new Error("Expected catalog to be valid.");
}

const request: TranslationRequest = {
  locale,
  fallbackLocales: [locale],
};
const paramOptions: TranslationParamOptions = {
  additionalUnsafeParamNames: ["customerId"],
};
const safeParams = safeTranslationParams({ name: "Ada" }, paramOptions);
void safeParams;

const translator: MessageTranslator = catalogMessageTranslator([catalogResult.value]);
const translated: Result<TranslatedMessage, I18nError> = translator.translate(
  messageDescriptor({
    code: "GREETING_HELLO",
    defaultMessage: "Hello {name}",
    messageKey: "greeting.hello",
    params: { name: "Ada" },
  }),
  request,
);
void translated;

const defaultTranslator: MessageTranslator = defaultMessageTranslator;
void defaultTranslator;

const errorCode: I18nErrorCode = "I18N_INVALID_TEMPLATE";
const explicitError: I18nError = i18nError({
  code: errorCode,
  defaultMessage: "Template is invalid.",
});
void explicitError;

// @ts-expect-error locale tags must be explicitly branded.
const invalidLocale: LocaleTag = "en-GB";
void invalidLocale;

// @ts-expect-error message templates must be explicitly branded.
const invalidTemplate: MessageTemplate = "Hello {name}";
void invalidTemplate;

// @ts-expect-error fallback locales must be branded locale tags.
const invalidRequest: TranslationRequest = { locale, fallbackLocales: ["fr-FR"] };
void invalidRequest;

// @ts-expect-error catalog messages must be strings or branded templates, not rich objects.
translationCatalog({ locale, messages: { "greeting.hello": { text: "Hello" } } });

// @ts-expect-error i18n error codes are constrained.
i18nError({ code: "I18N_BROKEN", defaultMessage: "Broken." });

const observedContexts: CoreI18nDiagnosticContext[] = [];
const diagnosticOptions: CoreI18nDiagnosticOptions = {
  diagnosticDefinitions: coreI18nDiagnosticDefinitions,
  onDiagnostic(_record, context) { observedContexts.push(context); return "observed"; },
};
localeTag("en-GB", diagnosticOptions);
messageTemplate("template", diagnosticOptions);
translationCatalog({ locale, messages: {} }, diagnosticOptions);
safeTranslationParams({ name: "Ada" }, paramOptions, diagnosticOptions);
interpolateMessageTemplate("{name}", { name: "Ada" }, diagnosticOptions);
const observedTranslator: MessageTranslator = catalogMessageTranslator([catalogResult.value], diagnosticOptions);
observedTranslator.translate(messageDescriptor({ code: "fixture", defaultMessage: "fixed" }), request, {});
defaultMessageTranslator.translate(messageDescriptor({ code: "fixture", defaultMessage: "fixed" }), request, diagnosticOptions);
i18nError({ code: "I18N_INVALID_TEMPLATE", defaultMessage: "fixed" }, diagnosticOptions);
const oldTranslatorImplementation: MessageTranslator = { translate(_message, oldRequest) { return { ok: true, value: { locale: oldRequest.locale, text: "fixed", source: "default-message" } }; } };
oldTranslatorImplementation.translate(messageDescriptor({ code: "fixture", defaultMessage: "fixed" }), request, diagnosticOptions);
const validationDetail: CoreI18nValidationDetail = { operation: "translation-catalog", field: "template", reason: "empty", effect: "predicate-rejected", ordinal: 0 };
const selectionDetail: CoreI18nSelectionDetail = { operation: "translate", phase: "source-selection", selection: "fallback-catalog", reason: "candidate-present", effect: "source-selected", ordinal: 2, catalogMisses: 1, templateMisses: 1 };
const boundaryDetail: CoreI18nBoundaryDetail = { operation: "interpolate", phase: "parameter-coercion", field: "parameter", reason: "threw", effect: "value-not-produced", ordinal: 1 };
coreI18nValidationDiagnosticRecord(validationDetail);
coreI18nSelectionDiagnosticRecord(selectionDetail);
coreI18nBoundaryDiagnosticRecord(boundaryDetail);
// @ts-expect-error diagnostic detail never admits submitted parameter names.
coreI18nValidationDiagnosticRecord({ ...validationDetail, parameterName: "private" });
// @ts-expect-error source selection does not establish completed translation.
coreI18nSelectionDiagnosticRecord({ ...selectionDetail, effect: "translation-completed" });
// @ts-expect-error raw boundary failures do not prove validation rejection.
coreI18nBoundaryDiagnosticRecord({ ...boundaryDetail, reason: "invalid-format" });
// @ts-expect-error submitted field names are not an approved location vocabulary.
coreI18nBoundaryDiagnosticRecord({ ...boundaryDetail, field: "customerId" });
// @ts-expect-error diagnostics do not replace the existing translation-param options argument.
safeTranslationParams({}, diagnosticOptions);
// @ts-expect-error runtime source definitions are immutable.
coreI18nDiagnosticDefinitions.push(coreI18nDiagnosticDefinitions[0]);
