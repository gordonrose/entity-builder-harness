import {
  brand,
  err,
  messageKey,
  ok,
  type Brand,
  type CoreError,
  type MessageDescriptor,
  type MessageKey,
  type MessageParamValue,
  type MessageParams,
  type Result,
} from "../shared/index";
import type { DiagnosticDescriptor } from "../diagnostics/index";

export type LocaleTag = Brand<string, "LocaleTag">;
export type MessageTemplate = Brand<string, "MessageTemplate">;

export type I18nErrorCode =
  | "I18N_INVALID_LOCALE"
  | "I18N_INVALID_TEMPLATE"
  | "I18N_MISSING_TEMPLATE_PARAM";

export interface I18nError extends CoreError {
  readonly code: I18nErrorCode;
}

export interface TranslationCatalog {
  readonly locale: LocaleTag;
  readonly messages: Readonly<Record<string, MessageTemplate>>;
}

export interface TranslationRequest {
  readonly locale: LocaleTag;
  readonly fallbackLocales?: readonly LocaleTag[];
}

export type TranslationSource = "catalog" | "default-message";

export interface TranslatedMessage {
  readonly locale: LocaleTag;
  readonly text: string;
  readonly source: TranslationSource;
  readonly messageKey?: MessageKey;
  readonly params?: MessageParams;
}

export interface MessageTranslator {
  translate(message: MessageDescriptor, request: TranslationRequest): Result<TranslatedMessage, I18nError>;
}

export function localeTag(value: string): Result<LocaleTag, I18nError> {
  if (!localeTagPattern.test(value)) {
    return err(
      i18nError({
        code: "I18N_INVALID_LOCALE",
        defaultMessage: "Locale tag must be a well-formed language tag.",
        messageKey: "i18n.locale.invalid",
        params: { locale: value },
      }),
    );
  }

  return ok(brand<string, "LocaleTag">(normalizeLocaleTag(value)));
}

export function messageTemplate(value: string): Result<MessageTemplate, I18nError> {
  if (value.length === 0) {
    return err(
      i18nError({
        code: "I18N_INVALID_TEMPLATE",
        defaultMessage: "Message template must be non-empty.",
        messageKey: "i18n.template.invalid",
      }),
    );
  }

  return ok(brand<string, "MessageTemplate">(value));
}

export function translationCatalog(input: {
  readonly locale: LocaleTag;
  readonly messages: Readonly<Record<string, string | MessageTemplate>>;
}): Result<TranslationCatalog, I18nError> {
  const messages: Record<string, MessageTemplate> = {};

  for (const [key, value] of Object.entries(input.messages)) {
    if (key.length === 0 || /\s/.test(key)) {
      return err(
        i18nError({
          code: "I18N_INVALID_TEMPLATE",
          defaultMessage: "Translation keys must be non-empty and must not contain whitespace.",
          messageKey: "i18n.translation_key.invalid",
          params: { key },
        }),
      );
    }

    const template = messageTemplate(value);

    if (!template.ok) {
      return template;
    }

    messages[key] = template.value;
  }

  return ok({
    locale: input.locale,
    messages,
  });
}

export const defaultMessageTranslator: MessageTranslator = {
  translate: (message, request) => translateDefaultMessage(message, request.locale),
};

export function catalogMessageTranslator(catalogs: readonly TranslationCatalog[]): MessageTranslator {
  const catalogByLocale = new Map<string, TranslationCatalog>(
    catalogs.map((catalog) => [
      catalog.locale,
      {
        locale: catalog.locale,
        messages: { ...catalog.messages },
      },
    ]),
  );

  return {
    translate(message, request) {
      const requestedLocales = [request.locale, ...(request.fallbackLocales ?? [])];

      if (message.messageKey !== undefined) {
        for (const requestedLocale of requestedLocales) {
          const catalog = catalogByLocale.get(requestedLocale);
          const template = catalog?.messages[message.messageKey];

          if (template !== undefined) {
            const rendered = interpolateMessageTemplate(template, message.params);

            if (!rendered.ok) {
              return rendered;
            }

            return ok({
              locale: requestedLocale,
              text: rendered.value,
              source: "catalog",
              messageKey: message.messageKey,
              ...(message.params === undefined ? {} : { params: message.params }),
            });
          }
        }
      }

      return translateDefaultMessage(message, request.locale);
    },
  };
}

export function interpolateMessageTemplate(
  template: string | MessageTemplate,
  params: MessageParams = {},
): Result<string, I18nError> {
  let missingParam: string | undefined;
  const rendered = template.replace(templateParamPattern, (match, rawParamName: string) => {
    if (!Object.prototype.hasOwnProperty.call(params, rawParamName)) {
      missingParam = rawParamName;
      return match;
    }

    return String(params[rawParamName] as MessageParamValue);
  });

  if (missingParam !== undefined) {
    return err(missingTemplateParamError(missingParam));
  }

  return ok(rendered);
}

export function i18nError(input: {
  readonly code: I18nErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly details?: Readonly<Record<string, unknown>>;
}): I18nError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}

const localeTagPattern = /^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$/;
const templateParamPattern = /\{([A-Za-z_][A-Za-z0-9_.-]*)\}/g;

function normalizeLocaleTag(value: string): string {
  const [language = value, ...subtags] = value.split("-");

  return [
    language.toLowerCase(),
    ...subtags.map((subtag) => {
      if (/^[A-Za-z]{2}$/.test(subtag) || /^\d{3}$/.test(subtag)) {
        return subtag.toUpperCase();
      }

      if (/^[A-Za-z]{4}$/.test(subtag)) {
        return `${subtag.charAt(0).toUpperCase()}${subtag.slice(1).toLowerCase()}`;
      }

      return subtag.toLowerCase();
    }),
  ].join("-");
}

function translateDefaultMessage(message: MessageDescriptor, locale: LocaleTag): Result<TranslatedMessage, I18nError> {
  const rendered = interpolateMessageTemplate(message.defaultMessage, message.params);

  if (!rendered.ok) {
    return rendered;
  }

  return ok({
    locale,
    text: rendered.value,
    source: "default-message",
    ...(message.messageKey === undefined ? {} : { messageKey: message.messageKey }),
    ...(message.params === undefined ? {} : { params: message.params }),
  });
}

function missingTemplateParamError(param: string): I18nError {
  return i18nError({
    code: "I18N_MISSING_TEMPLATE_PARAM",
    defaultMessage: "Message template parameter is missing.",
    messageKey: "i18n.template_param.missing",
    params: { param },
  });
}
