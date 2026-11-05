import { deepEqual, equal, throws } from "node:assert/strict";
import { createDiagnosticRecord, defineDiagnostic, diagnosticDescriptor, parseDiagnosticRecord, type DiagnosticRecord } from "../src/diagnostics/index";
import {
  catalogMessageTranslator,
  defaultMessageTranslator,
  i18nError,
  interpolateMessageTemplate,
  localeTag,
  messageTemplate,
  safeTranslationParams,
  translationCatalog,
  coreI18nDiagnosticDefinitions,
  coreI18nValidationDiagnostic,
  coreI18nSelectionDiagnostic,
  coreI18nBoundaryDiagnostic,
  coreI18nValidationDiagnosticRecord,
  coreI18nSelectionDiagnosticRecord,
  coreI18nBoundaryDiagnosticRecord,
  type CoreI18nDiagnosticOptions,
  type CoreI18nDiagnosticContext,
  type CoreI18nValidationDetail,
  type TranslationCatalog,
  type LocaleTag,
} from "../src/i18n/index";
import { secretString } from "../src/security/index";
import { isErr, isOk, messageDescriptor, messageKey, type MessageDescriptor, type MessageParams } from "../src/shared/index";

const english = localeTag("en-us");
equal(isOk(english), true);
if (!isOk(english)) {
  throw new Error("Expected en-us to be a valid locale tag.");
}
equal(english.value, "en-US");

const french = localeTag("fr");
equal(isOk(french), true);
if (!isOk(french)) {
  throw new Error("Expected fr to be a valid locale tag.");
}

const invalidLocale = localeTag("en_US");
equal(isErr(invalidLocale), true);
if (!isErr(invalidLocale)) {
  throw new Error("Expected en_US to fail.");
}
equal(invalidLocale.error.code, "I18N_INVALID_LOCALE");

const invalidTemplate = messageTemplate("");
equal(isErr(invalidTemplate), true);
if (!isErr(invalidTemplate)) {
  throw new Error("Expected empty template to fail.");
}
equal(invalidTemplate.error.code, "I18N_INVALID_TEMPLATE");

const mutableMessages = {
  "validation.required": "{field} is required.",
};
const catalog = translationCatalog({
  locale: english.value,
  messages: mutableMessages,
});
equal(isOk(catalog), true);
if (!isOk(catalog)) {
  throw new Error("Expected translation catalog to be valid.");
}
mutableMessages["validation.required"] = "changed";

const translator = catalogMessageTranslator([catalog.value]);
const requiredMessage = messageDescriptor({
  code: "VALIDATION_REQUIRED",
  defaultMessage: "Field is required.",
  messageKey: "validation.required",
  params: { field: "Email" },
});
const translated = translator.translate(requiredMessage, { locale: english.value });
equal(isOk(translated), true);
if (!isOk(translated)) {
  throw new Error("Expected catalog translation to succeed.");
}
deepEqual(translated.value, {
  locale: "en-US",
  text: "Email is required.",
  source: "catalog",
  messageKey: "validation.required",
  paramKeys: ["field"],
});

const fallbackMessage = messageDescriptor({
  code: "VALIDATION_REQUIRED",
  defaultMessage: "{field} is required.",
  messageKey: "validation.required",
  params: { field: "Email" },
});
const fallback = translator.translate(fallbackMessage, { locale: french.value, fallbackLocales: [english.value] });
equal(isOk(fallback), true);
if (!isOk(fallback)) {
  throw new Error("Expected fallback translation to succeed.");
}
equal(fallback.value.locale, "en-US");
equal(fallback.value.source, "catalog");

const missingTranslation = translator.translate(
  messageDescriptor({
    code: "VALIDATION_MIN_LENGTH",
    defaultMessage: "{field} is too short.",
    messageKey: "validation.min_length",
    params: { field: "Password" },
  }),
  { locale: french.value },
);
equal(isOk(missingTranslation), true);
if (!isOk(missingTranslation)) {
  throw new Error("Expected missing translation to use default message.");
}
deepEqual(missingTranslation.value, {
  locale: "fr",
  text: "Password is too short.",
  source: "default-message",
  messageKey: "validation.min_length",
  paramKeys: ["field"],
});

const defaultOnly = defaultMessageTranslator.translate(requiredMessage, { locale: english.value });
equal(isOk(defaultOnly), true);
if (!isOk(defaultOnly)) {
  throw new Error("Expected default-message translator to succeed.");
}
equal(defaultOnly.value.source, "default-message");

const missingParam = interpolateMessageTemplate("{field} is required.", {});
equal(isErr(missingParam), true);
if (!isErr(missingParam)) {
  throw new Error("Expected missing template param to fail.");
}
equal(missingParam.error.code, "I18N_MISSING_TEMPLATE_PARAM");
deepEqual(missingParam.error.params, { param: "field" });

const unsafeParam = interpolateMessageTemplate("Token {token}", {
  token: secretString("super-secret-token"),
});
equal(isErr(unsafeParam), true);
if (!isErr(unsafeParam)) {
  throw new Error("Expected unsafe template param to fail.");
}
equal(unsafeParam.error.code, "I18N_UNSAFE_TEMPLATE_PARAM");
deepEqual(unsafeParam.error.params, { param: "token" });

const unsafeRawIdentifier = safeTranslationParams({
  userId: "user-123",
});
equal(isErr(unsafeRawIdentifier), true);
if (!isErr(unsafeRawIdentifier)) {
  throw new Error("Expected raw identifier param to fail.");
}
equal(unsafeRawIdentifier.error.code, "I18N_UNSAFE_TEMPLATE_PARAM");

const diagnostic = diagnosticDescriptor({
  failureKind: "validation",
  failureSource: "app",
  severity: "warning",
  recovery: "user_correctable",
});
const explicitError = i18nError({
  code: "I18N_INVALID_TEMPLATE",
  defaultMessage: "Template is invalid.",
  diagnostic,
});
equal(explicitError.diagnostic, diagnostic);

console.log("packages/core i18n runtime test passed.");

// Closed owned records, not copies of legacy params, templates or rendered text.
const englishLocale: LocaleTag = english.value;
const frenchLocale: LocaleTag = french.value;
function validation(detail: Omit<CoreI18nValidationDetail, "effect">): DiagnosticRecord {
  return { schema: "core/diagnostic-record/v1", code: "core.i18n.validation-rejected", definitionVersion: 1,
    detail: { ...detail, effect: "predicate-rejected" } };
}
function boundary(operation: string, phase: string, field?: string, ordinal?: number): DiagnosticRecord {
  return { schema: "core/diagnostic-record/v1", code: "core.i18n.boundary-failed", definitionVersion: 1,
    detail: { operation, phase, reason: "threw", effect: "value-not-produced", ...(field === undefined ? {} : { field }), ...(ordinal === undefined ? {} : { ordinal }) } };
}
function caught(action: () => unknown): unknown { try { action(); } catch (error) { return error; } throw new Error("Expected raw failure."); }
const records: DiagnosticRecord[] = [];
const contexts: CoreI18nDiagnosticContext[] = [];
const observations: CoreI18nDiagnosticOptions = { onDiagnostic(record, context) {
  equal(this, observations); equal(Object.isFrozen(context), true); records.push(record); contexts.push(context);
  return "observed";
} };
const clear = () => { records.length = 0; contexts.length = 0; };
for (const [result, detail] of [
  [localeTag("en_US", observations), { operation: "locale-tag", field: "locale", reason: "invalid-format" }],
  [messageTemplate("", observations), { operation: "message-template", field: "template", reason: "empty" }],
  [translationCatalog({ locale: english.value, messages: { valid: "ok", "": "bad" } }, observations), { operation: "translation-catalog", field: "catalog-key", reason: "empty", ordinal: 1 }],
  [translationCatalog({ locale: english.value, messages: { "bad key": "x" } }, observations), { operation: "translation-catalog", field: "catalog-key", reason: "contains-whitespace", ordinal: 0 }],
  [translationCatalog({ locale: english.value, messages: { valid: "ok", empty: "" } }, observations), { operation: "translation-catalog", field: "template", reason: "empty", ordinal: 1 }],
  [safeTranslationParams({ safe: 1, "ACCESS-token": "private-canary" }, undefined, observations), { operation: "translation-params", field: "parameter", reason: "unsafe-name", ordinal: 1 }],
  [interpolateMessageTemplate("{first} {present} {last}", { present: false }, observations), { operation: "interpolate", field: "parameter", reason: "missing-own-property", ordinal: 2 }],
] as const) {
  equal(result.ok, false);
  if (!result.ok) deepEqual(result.error.diagnosticRecord, validation(detail));
}
equal(records.length, 7);
const lastMissing = interpolateMessageTemplate("{first} {last}");
if (!lastMissing.ok) deepEqual(lastMissing.error.params, { param: "last" }); else throw new Error("Expected last missing.");
deepEqual(coreI18nValidationDiagnostic.classification, { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
deepEqual(coreI18nSelectionDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none", retryable: false, userCorrectable: false });
deepEqual(coreI18nBoundaryDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
equal(Object.isFrozen(coreI18nDiagnosticDefinitions), true);
deepEqual(coreI18nDiagnosticDefinitions.map(({ code, version }) => [code, version]), [
  ["core.i18n.validation-rejected", 1], ["core.i18n.selection-observed", 1], ["core.i18n.boundary-failed", 1],
]);
for (const [definition, record] of [
  [coreI18nValidationDiagnostic, coreI18nValidationDiagnosticRecord({ operation: "locale-tag", field: "locale", reason: "invalid-format", effect: "predicate-rejected" })],
  [coreI18nSelectionDiagnostic, coreI18nSelectionDiagnosticRecord({ operation: "translate", phase: "source-selection", selection: "default-message", reason: "no-message-key", effect: "source-selected" })],
  [coreI18nBoundaryDiagnostic, coreI18nBoundaryDiagnosticRecord({ operation: "interpolate", phase: "interpolation", reason: "threw", effect: "value-not-produced" })],
] as const) {
  equal(parseDiagnosticRecord<unknown>(definition, record).ok, true);
  for (const detail of [{ ...record.detail, text: "private-canary" }, { ...record.detail, ordinal: -1 }, { ...record.detail, ordinal: 0.5 }, { ...record.detail, effect: "translated" }, { ...record.detail, field: "private-param-name" }]) {
    equal(parseDiagnosticRecord<unknown>(definition, { ...record, detail }).ok, false);
  }
}
equal(createDiagnosticRecord(coreI18nSelectionDiagnostic, { operation: "translate", phase: "source-selection", selection: "default-message", reason: "no-candidate-match", effect: "source-selected", catalogMisses: -1 }).ok, false);
let observedAccessor = 0;
equal(createDiagnosticRecord(coreI18nValidationDiagnostic, Object.defineProperty({}, "operation", { get() { observedAccessor++; return "locale-tag"; } }) as never).ok, false);
equal(observedAccessor, 0);

// Eager enumeration beats an earlier invalid key; locale is read only on success.
clear(); const eagerError = Object.freeze(new Error("private-catalog-canary")); const catalogReads: string[] = [];
const eagerMessages = { "bad key": "invalid", get later(): never { catalogReads.push("later"); throw eagerError; } };
equal(caught(() => translationCatalog({ get locale() { catalogReads.push("locale"); return english.value; }, messages: eagerMessages }, observations)), eagerError);
deepEqual(catalogReads, ["later"]);
deepEqual(records, [boundary("translation-catalog", "catalog-enumeration", "messages")]);
clear(); let parameterReads = 0;
const unsafeUnused = safeTranslationParams({ get safe() { parameterReads++; return "x"; }, user_id: "private-canary" }, undefined, observations);
equal(unsafeUnused.ok, false); equal(parameterReads, 0);
equal(safeTranslationParams({ customerId: "x" }, { additionalUnsafeParamNames: ["customer-id"] }).ok, false);
equal(safeTranslationParams({ tokenCount: 2 }).ok, true);
equal(messageTemplate(" ").ok, true);
equal(localeTag("zz-ZZ").ok, true);
deepEqual(interpolateMessageTemplate("{a}/{b}/{c}/{d}", { a: null, b: false, c: 0, d: "" }), { ok: true, value: "null/false/0/" });
deepEqual(interpolateMessageTemplate("literal {1invalid} {broken"), { ok: true, value: "literal {1invalid} {broken" });
const coercionError = Object.freeze(new Error("private-value-canary")); clear();
const coercedParams = { value: { toString() { throw coercionError; } } } as unknown as MessageParams;
equal(caught(() => interpolateMessageTemplate("{missing} {value}", coercedParams, observations)), coercionError);
deepEqual(records, [boundary("interpolate", "parameter-coercion", "parameter", 1)]);
// Custom replace callbacks do not get to change sentinel or ordinal semantics.
clear();
const sentinelTemplate = { replace(_pattern: unknown, callback: (match: string, name: unknown) => string) { callback("x", undefined); return "unchanged"; } } as unknown as string;
deepEqual(interpolateMessageTemplate(sentinelTemplate, {}, observations), { ok: true, value: "unchanged" });
deepEqual(records, [] as DiagnosticRecord[]);
const customTemplate = { replace(_pattern: unknown, callback: (match: string, name: string, index: number) => string) { callback("x", "first", 900); callback("y", "last", -1); return "ignored"; } } as unknown as string;
const customMissing = interpolateMessageTemplate(customTemplate, {}, observations);
if (!customMissing.ok) deepEqual(customMissing.error.diagnosticRecord, validation({ operation: "interpolate", field: "parameter", reason: "missing-own-property", ordinal: 1 })); else throw new Error("Expected missing.");

// Bound defaults and invocation overrides; only first selected candidate renders.
clear();
const plainCatalog = (locale: LocaleTag, messages: Record<string, string>) => ({ locale, messages }) as TranslationCatalog;
const bound = catalogMessageTranslator([plainCatalog(englishLocale, { present: "old" }), plainCatalog(frenchLocale, {}), plainCatalog(englishLocale, { present: "new" })], observations);
const presentMessage = messageDescriptor({ code: "fixture", messageKey: "present", defaultMessage: "default" });
deepEqual(bound.translate(presentMessage, { locale: english.value }), { ok: true, value: { locale: "en-US", text: "new", source: "catalog", messageKey: "present" } });
deepEqual(records, [{ schema: "core/diagnostic-record/v1", code: "core.i18n.selection-observed", definitionVersion: 1,
  detail: { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "requested-catalog", reason: "candidate-present", ordinal: 0, catalogMisses: 0, templateMisses: 0 } }]);
clear(); bound.translate(presentMessage, { locale: english.value }, {}); deepEqual(records, [] as DiagnosticRecord[]);
bound.translate(presentMessage, { locale: english.value }, undefined); equal(records.length, 1); clear();
const invocationRecords: DiagnosticRecord[] = [];
bound.translate(presentMessage, { locale: english.value }, { onDiagnostic(record) { invocationRecords.push(record); } });
equal(invocationRecords.length, 1); deepEqual(records, [] as DiagnosticRecord[]);
const german = localeTag("de"); if (!german.ok) throw new Error("Expected de.");
bound.translate(presentMessage, { locale: german.value, fallbackLocales: [french.value, french.value, english.value] });
deepEqual(records[0]?.detail, { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "fallback-catalog", reason: "candidate-present", ordinal: 3, catalogMisses: 1, templateMisses: 2 });
clear(); bound.translate(messageDescriptor({ code: "fixture", messageKey: "absent", defaultMessage: "default" }), { locale: french.value });
deepEqual(records[0]?.detail, { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "default-message", reason: "no-candidate-match", catalogMisses: 0, templateMisses: 1 });
clear(); bound.translate(messageDescriptor({ code: "fixture", defaultMessage: "default" }), { locale: french.value });
deepEqual(records[0]?.detail, { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "default-message", reason: "no-message-key", catalogMisses: 0, templateMisses: 0 });
clear(); defaultMessageTranslator.translate(presentMessage, { locale: english.value }, observations);
deepEqual(records[0]?.detail, { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "default-message", reason: "default-translator" });
clear();
const noRetry = catalogMessageTranslator([plainCatalog(english.value, { present: "{missing}" }), plainCatalog(french.value, { present: "valid" })], observations);
const failedRender = noRetry.translate(presentMessage, { locale: english.value, fallbackLocales: [french.value] });
equal(failedRender.ok, false); equal(records.length, 2);
deepEqual(records[0]?.detail, { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "requested-catalog", reason: "candidate-present", ordinal: 0, catalogMisses: 0, templateMisses: 0 });
deepEqual(records[1], validation({ operation: "interpolate", field: "parameter", reason: "missing-own-property", ordinal: 0 }));

// Optional lookup skips messageKey on absent catalogs; no cache/re-read for diagnosis.
clear(); let keyReads = 0;
const changingKey = { code: "fixture", defaultMessage: "default", get messageKey() { keyReads++; return keyReads <= 2 ? "present" : "returned-key"; } } as MessageDescriptor;
const changed = bound.translate(changingKey, { locale: german.value, fallbackLocales: [english.value] });
equal(keyReads, 3); equal(changed.ok, true);
if (changed.ok) equal(changed.value.messageKey, "returned-key");
clear(); const requestFailure = Object.freeze(new Error("private-fallback-canary"));
equal(caught(() => bound.translate(messageDescriptor({ code: "fixture", defaultMessage: "ok" }), { locale: english.value, get fallbackLocales(): never { throw requestFailure; } }, observations)), requestFailure);
deepEqual(records, [boundary("translate", "input-projection", "fallback-locales")]);
clear();
const inherited = catalogMessageTranslator([plainCatalog(english.value, {})], observations);
const inheritedError = caught(() => inherited.translate(messageDescriptor({ code: "fixture", messageKey: "toString", defaultMessage: "must-not-fallback" }), { locale: english.value }));
equal(inheritedError instanceof TypeError, true);
equal(records[0]?.code, "core.i18n.selection-observed");
equal(records.some((record) => record.code === "core.i18n.validation-rejected"), false);

// Original member selection/receiver and native noncallable error text survive.
const noncallableTemplate = { replace: 1 } as unknown as string;
function originalReplace(template: string) { return template.replace(/x/, "x"); }
const originalReplaceError = caught(() => originalReplace(noncallableTemplate)) as Error;
equal((caught(() => interpolateMessageTemplate(noncallableTemplate)) as Error).message, originalReplaceError.message);
const catalogs = { map: 1 } as unknown as readonly TranslationCatalog[];
const originalMapError = caught(() => catalogs.map((catalog) => catalog)) as Error;
equal((caught(() => catalogMessageTranslator(catalogs)) as Error).message, originalMapError.message);
let replaceReceiver: unknown;
const receiverTemplate = { replace(_pattern: unknown, callback: (match: string, name: string) => string) { replaceReceiver = this; return callback("{value}", "value"); } } as unknown as string;
deepEqual(interpolateMessageTemplate(receiverTemplate, { value: 7 }), { ok: true, value: "7" }); equal(replaceReceiver, receiverTemplate);
clear(); const afterMapError = Object.freeze(new Error("private-after-map"));
const customCatalogs = { map(callback: (catalog: TranslationCatalog, index: number) => unknown) { equal(this, customCatalogs); callback(plainCatalog(english.value, {}), 999); throw afterMapError; } } as unknown as readonly TranslationCatalog[];
equal(caught(() => catalogMessageTranslator(customCatalogs, observations)), afterMapError);
deepEqual(records, [boundary("catalog-translator", "catalog-copy", "catalogs")]);
clear(); const indexError = Object.freeze(new Error("private-index"));
const returnedEntries = { [Symbol.iterator]() { throw indexError; } };
const customEntries = { map(callback: (catalog: TranslationCatalog) => unknown) { callback(plainCatalog(english.value, {})); return returnedEntries; } } as unknown as readonly TranslationCatalog[];
equal(caught(() => catalogMessageTranslator(customEntries, observations)), indexError);
deepEqual(records, [boundary("catalog-translator", "catalog-index", "catalogs")]);

// Each raw location is established by the actual failing expression, never a replay.
clear(); const raw = Object.freeze(new Error("private-stage-canary"));
equal(caught(() => defaultMessageTranslator.translate(presentMessage, { get locale(): never { throw raw; } }, observations)), raw);
deepEqual(records.slice(-1), [boundary("translate", "input-projection", "locale")]);
clear();
const normalizeInput = { toString() { return "en"; }, split() { throw raw; } } as unknown as string;
equal(caught(() => localeTag(normalizeInput, observations)), raw);
deepEqual(records, [boundary("locale-tag", "normalization", "locale")]);
clear();
equal(caught(() => safeTranslationParams({}, { get additionalUnsafeParamNames(): never { throw raw; } }, observations)), raw);
deepEqual(records, [boundary("translation-params", "unsafe-name-declaration", "additional-unsafe-param-names")]);
clear(); const enumerationInput = new Proxy({}, { ownKeys() { throw raw; } });
equal(caught(() => safeTranslationParams(enumerationInput, undefined, observations)), raw);
deepEqual(records, [boundary("translation-params", "parameter-enumeration", "params")]);
clear();
equal(caught(() => safeTranslationParams({ get value(): never { throw raw; } }, undefined, observations)), raw);
deepEqual(records, [boundary("translation-params", "parameter-copy", "params")]);
clear(); let keyLookupReads = 0;
equal(caught(() => bound.translate({ code: "fixture", defaultMessage: "fixed", get messageKey() { if (++keyLookupReads === 2) throw raw; return "present"; } } as MessageDescriptor, { locale: english.value })), raw);
equal(keyLookupReads, 2); deepEqual(records, [boundary("translate", "input-projection", "message-key", 0)]);
clear(); const originalGet = Map.prototype.get;
try {
  Map.prototype.get = function () { throw raw; };
  equal(caught(() => bound.translate(presentMessage, { locale: english.value })), raw);
} finally { Map.prototype.get = originalGet; }
deepEqual(records, [boundary("translate", "catalog-lookup", "catalog", 0)]);
clear(); let nullishKeyReads = 0;
try {
  Map.prototype.get = function (this: Map<unknown, unknown>, key: unknown) { return key === german.value ? null : Reflect.apply(originalGet, this, [key]); };
  bound.translate({ code: "fixture", defaultMessage: "fixed", get messageKey() { nullishKeyReads++; return "present"; } } as MessageDescriptor, { locale: german.value, fallbackLocales: [english.value] });
} finally { Map.prototype.get = originalGet; }
equal(nullishKeyReads, 3);
deepEqual(records[0]?.detail, { operation: "translate", phase: "source-selection", effect: "source-selected", selection: "fallback-catalog", reason: "candidate-present", ordinal: 1, catalogMisses: 1, templateMisses: 0 });
clear(); let messagesKeyReads = 0;
try {
  Map.prototype.get = function () { return { get messages() { throw raw; } }; };
  equal(caught(() => bound.translate({ code: "fixture", defaultMessage: "fixed", get messageKey() { messagesKeyReads++; return "present"; } } as MessageDescriptor, { locale: english.value })), raw);
} finally { Map.prototype.get = originalGet; }
equal(messagesKeyReads, 1); deepEqual(records, [boundary("translate", "input-projection", "messages", 0)]);
clear();
try {
  Map.prototype.get = function () { return { messages: new Proxy({}, { get() { throw raw; } }) }; };
  equal(caught(() => bound.translate(presentMessage, { locale: english.value })), raw);
} finally { Map.prototype.get = originalGet; }
deepEqual(records, [boundary("translate", "template-lookup", "template", 0)]);
clear();
const throwingFallback = { [Symbol.iterator]() { throw raw; } } as unknown as readonly typeof english.value[];
equal(caught(() => bound.translate(presentMessage, { locale: english.value, fallbackLocales: throwingFallback })), raw);
deepEqual(records, [boundary("translate", "candidate-iteration", "fallback-locales")]);
clear();
const throwingCatalog = catalogMessageTranslator([plainCatalog(english.value, { present: "{value}" })], observations);
equal(caught(() => throwingCatalog.translate({ code: "fixture", defaultMessage: "fixed", messageKey: messageKey("present"), params: coercedParams }, { locale: english.value })), coercionError);
deepEqual(records.slice(1), [boundary("interpolate", "parameter-coercion", "parameter", 0), boundary("translate", "interpolation", "template", 0)]);
clear();
equal(caught(() => defaultMessageTranslator.translate({ code: "fixture", defaultMessage: "{value}", params: coercedParams }, { locale: english.value }, observations)), coercionError);
deepEqual(records.slice(1), [boundary("interpolate", "parameter-coercion", "parameter", 0), boundary("translate", "interpolation", "template")]);
clear();
const afterReplace = { replace(_pattern: unknown, callback: (match: string, name: string) => string) { callback("{value}", "value"); throw raw; } } as unknown as string;
equal(caught(() => interpolateMessageTemplate(afterReplace, { value: 1 }, observations)), raw);
deepEqual(records, [boundary("interpolate", "interpolation", "template")]);
clear(); let paramsReads = 0;
equal(caught(() => bound.translate({ code: "fixture", defaultMessage: "fixed", messageKey: messageKey("present"), get params() { if (++paramsReads === 2) throw raw; return {}; } }, { locale: english.value })), raw);
equal(paramsReads, 2); deepEqual(records.slice(-1), [boundary("translate", "result-projection", "params")]);
const factoryReads: string[] = [];
const readCatalog = { get locale() { factoryReads.push("locale"); return english.value; }, get messages() { factoryReads.push("messages"); return {}; } };
catalogMessageTranslator([readCatalog]); deepEqual(factoryReads, ["locale", "locale", "messages"]);
const defaultReads: string[] = [];
defaultMessageTranslator.translate({ code: "fixture", get defaultMessage() { defaultReads.push("defaultMessage"); return "fixed"; }, get params() { defaultReads.push("params"); return {}; }, get messageKey() { defaultReads.push("messageKey"); return undefined; } } as unknown as MessageDescriptor, { get locale() { defaultReads.push("locale"); return english.value; } });
deepEqual(defaultReads, ["locale", "defaultMessage", "params", "messageKey", "params"]);
clear(); let outputEnumeration = 0;
const changingParams = new Proxy({ value: 1 }, { ownKeys(target) { if (++outputEnumeration === 3) throw raw; return Reflect.ownKeys(target); } });
equal(caught(() => bound.translate({ code: "fixture", defaultMessage: "fixed", messageKey: messageKey("present"), params: changingParams }, { locale: english.value })), raw);
equal(outputEnumeration, 3); deepEqual(records.slice(-1), [boundary("translate", "parameter-enumeration", "params")]);

// Old error input shape/read counts and old primary identity remain unchanged.
const oldPrimary = coreI18nValidationDiagnosticRecord({ operation: "locale-tag", field: "locale", reason: "invalid-format", effect: "predicate-rejected" });
const errorReads: string[] = [];
const legacyInput = new Proxy({ code: "I18N_INVALID_TEMPLATE" as const, defaultMessage: "fixed", messageKey: "fixture.key", params: {}, cause: {}, diagnostic, diagnosticRecord: oldPrimary, details: {} }, { get(target, key, receiver) { errorReads.push(String(key)); return Reflect.get(target, key, receiver); } });
const retained = i18nError(legacyInput, observations);
equal(retained.diagnosticRecord, oldPrimary);
deepEqual(errorReads, ["code", "defaultMessage", "messageKey", "messageKey", "params", "params", "cause", "cause", "diagnostic", "diagnostic", "diagnosticRecord", "diagnosticRecord", "details", "details"]);
clear(); const errorProjection = Object.freeze(new Error("private-error-projection"));
equal(caught(() => i18nError({ code: "I18N_INVALID_TEMPLATE", get defaultMessage(): never { throw errorProjection; } }, observations)), errorProjection);
deepEqual(records, [boundary("error", "error-projection", "default-message")]);

// Own and selected primary/eight are independent; malformed/accessor evidence is not read.
const sourceDefinition = defineDiagnostic({ code: "fixture.i18n.source", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
});
const sourceRecords = Array.from({ length: 9 }, (_, ordinal) => { const record = createDiagnosticRecord(sourceDefinition, { ordinal }); if (!record.ok) throw new Error("fixture"); return record.value; });
const sourceFailure = Object.freeze({ diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1), message: "private-source-canary" });
const selectedRecords: DiagnosticRecord[] = [];
const selectedOptions: CoreI18nDiagnosticOptions = { diagnosticDefinitions: [sourceDefinition], onDiagnostic(record) { equal(this, selectedOptions); selectedRecords.push(record); } };
const lengthFailure = { get length() { throw sourceFailure; } } as unknown as string;
equal(caught(() => messageTemplate(lengthFailure, selectedOptions)), sourceFailure);
deepEqual(selectedRecords, [boundary("message-template", "predicate-invocation", "template"), ...sourceRecords]);
equal(selectedRecords.length, 10); equal(JSON.stringify(selectedRecords).includes("private-"), false);
equal(selectedRecords[1] === sourceRecords[0], false);
equal(Object.isFrozen(selectedRecords[1]), true);
let attemptedDelivery = 0; const afterFailedOwn: DiagnosticRecord[] = [];
equal(caught(() => messageTemplate(lengthFailure, { diagnosticDefinitions: [sourceDefinition], onDiagnostic(record) { if (++attemptedDelivery === 1) throw new Error("private-own-sink"); afterFailedOwn.push(record); } })), sourceFailure);
equal(attemptedDelivery, 10); deepEqual(afterFailedOwn, sourceRecords);
clear(); equal(caught(() => messageTemplate(lengthFailure, observations)), sourceFailure); equal(records.length, 1);
selectedRecords.length = 0;
let sourceAccessorReads = 0;
const accessorFailure = Object.freeze(Object.defineProperty({ relatedDiagnosticRecords: sourceRecords.slice(1) }, "diagnosticRecord", { get() { sourceAccessorReads++; throw new Error("private-accessor"); } }));
equal(caught(() => messageTemplate({ get length() { throw accessorFailure; } } as unknown as string, selectedOptions)), accessorFailure);
equal(sourceAccessorReads, 0); deepEqual(selectedRecords.slice(1, 9), sourceRecords.slice(1));
deepEqual(selectedRecords[9], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-inaccessible" } });
selectedRecords.length = 0;
const malformedFailure = Object.freeze({ diagnosticRecord: { ...sourceRecords[0], raw: "private-canary" }, relatedDiagnosticRecords: [sourceRecords[1], { code: "unknown" }] });
equal(caught(() => messageTemplate({ get length() { throw malformedFailure; } } as unknown as string, selectedOptions)), malformedFailure);
deepEqual(selectedRecords.slice(1), [sourceRecords[1], { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1, detail: { reason: "evidence-rejected" } }]);
for (const raw of ["private-primitive", undefined, Object.freeze(new Error("private-frozen"))]) {
  clear(); equal(caught(() => messageTemplate({ get length() { throw raw; } } as unknown as string, observations)), raw);
  deepEqual(records, [boundary("message-template", "predicate-invocation", "template")]);
}
throws(() => coreI18nSelectionDiagnosticRecord({ operation: "translate", phase: "source-selection", selection: "default-message", reason: "no-message-key", effect: "source-selected", ordinal: -1 }), /CORE_I18N_DIAGNOSTIC_INVALID/);

async function proveObserverIsolation(): Promise<void> {
  const unhandled: unknown[] = []; const listener = (error: unknown) => { unhandled.push(error); };
  process.on("unhandledRejection", listener);
  try {
    for (const sink of [
      () => { throw new Error("private-sync-sink"); },
      () => Promise.reject(new Error("private-native-sink")),
      () => { const promise = Promise.reject(new Error("private-shadowed-sink")); Object.defineProperty(promise, "then", { get() { throw new Error("private-shadowed-then"); } }); return promise; },
      () => ({ then(_resolve: unknown, reject: (error: unknown) => void) { reject(new Error("private-thenable-rejection")); } }),
      () => ({ then() { throw new Error("private-thenable-throw"); } }),
      () => Object.defineProperty({}, "then", { get() { throw new Error("private-then-getter"); } }),
    ]) {
      const options: CoreI18nDiagnosticOptions = { onDiagnostic() { equal(this, options); return sink(); } };
      equal(localeTag("en_US", options).ok, false);
      deepEqual(defaultMessageTranslator.translate(presentMessage, { locale: englishLocale }, options), { ok: true, value: { locale: englishLocale, text: "default", source: "default-message", messageKey: "present" } });
      equal(caught(() => messageTemplate(lengthFailure, options)), sourceFailure);
    }
    await new Promise<void>((resolve) => setImmediate(resolve));
    await new Promise<void>((resolve) => setImmediate(resolve));
    deepEqual(unhandled, []);
  } finally { process.removeListener("unhandledRejection", listener); }
}
void proveObserverIsolation().then(() => console.log("Core i18n diagnostic alternatives, ordering and isolation passed."), (error: unknown) => { console.error(error); process.exitCode = 1; });
