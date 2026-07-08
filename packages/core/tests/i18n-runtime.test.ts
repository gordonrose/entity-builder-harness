import { deepEqual, equal } from "node:assert/strict";
import { diagnosticDescriptor } from "../src/diagnostics/index";
import {
  catalogMessageTranslator,
  defaultMessageTranslator,
  i18nError,
  interpolateMessageTemplate,
  localeTag,
  messageTemplate,
  translationCatalog,
} from "../src/i18n/index";
import { isErr, isOk, messageDescriptor } from "../src/shared/index";

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
  params: { field: "Email" },
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
  params: { field: "Password" },
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
