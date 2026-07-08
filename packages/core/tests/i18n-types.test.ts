import {
  catalogMessageTranslator,
  defaultMessageTranslator,
  i18nError,
  localeTag,
  messageTemplate,
  translationCatalog,
  type I18nError,
  type I18nErrorCode,
  type LocaleTag,
  type MessageTemplate,
  type MessageTranslator,
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
