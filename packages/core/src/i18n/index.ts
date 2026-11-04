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
import { I18nObservation } from "./observations";
import type { CoreI18nDiagnosticOptions, CoreI18nValidationDetail } from "./diagnostics";
export * from "./diagnostics";

export type LocaleTag = Brand<string, "LocaleTag">;
export type MessageTemplate = Brand<string, "MessageTemplate">;

export type I18nErrorCode =
  | "I18N_INVALID_LOCALE"
  | "I18N_INVALID_TEMPLATE"
  | "I18N_MISSING_TEMPLATE_PARAM"
  | "I18N_UNSAFE_TEMPLATE_PARAM";

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
  readonly paramKeys?: readonly string[];
}

export interface MessageTranslator {
  translate(message: MessageDescriptor, request: TranslationRequest, diagnostics?: CoreI18nDiagnosticOptions): Result<TranslatedMessage, I18nError>;
}

export interface TranslationParamOptions {
  readonly additionalUnsafeParamNames?: readonly string[];
}

export const defaultUnsafeTranslationParamNames = [
  "password",
  "passphrase",
  "passwd",
  "pwd",
  "secret",
  "clientSecret",
  "token",
  "accessToken",
  "refreshToken",
  "idToken",
  "sessionToken",
  "apiKey",
  "authorization",
  "cookie",
  "setCookie",
  "privateKey",
  "credential",
  "credentials",
  "email",
  "phone",
  "userId",
  "principalId",
  "requestId",
  "correlationId",
  "traceId",
  "sessionId",
  "ipAddress",
  "rawRequest",
  "requestBody",
] as const;

export function localeTag(value: string, diagnostics?: CoreI18nDiagnosticOptions): Result<LocaleTag, I18nError> {
  const observation = new I18nObservation("locale-tag", diagnostics);
  return observation.run(() => {
  observation.location("predicate-invocation", "locale");
  if (!localeTagPattern.test(value)) {
    return err(
      observation.rejected(i18nError({
        code: "I18N_INVALID_LOCALE",
        defaultMessage: "Locale tag must be a well-formed language tag.",
        messageKey: "i18n.locale.invalid",
        params: { locale: value },
      }), { operation: "locale-tag", field: "locale", reason: "invalid-format" }),
    );
  }

  observation.location("normalization", "locale");
  return ok(brand<string, "LocaleTag">(normalizeLocaleTag(value)));
  });
}

export function messageTemplate(value: string, diagnostics?: CoreI18nDiagnosticOptions): Result<MessageTemplate, I18nError> {
  return messageTemplateAt(value, diagnostics, "message-template");
}

function messageTemplateAt(value: string, diagnostics: CoreI18nDiagnosticOptions | undefined,
  operation: "message-template" | "translation-catalog", ordinal?: number): Result<MessageTemplate, I18nError> {
  const observation = new I18nObservation(operation, diagnostics);
  return observation.run(() => {
  observation.location("predicate-invocation", "template", ordinal);
  if (value.length === 0) {
    return err(
      observation.rejected(i18nError({
        code: "I18N_INVALID_TEMPLATE",
        defaultMessage: "Message template must be non-empty.",
        messageKey: "i18n.template.invalid",
      }), { operation, field: "template", reason: "empty", ...(ordinal === undefined ? {} : { ordinal }) }),
    );
  }

  return ok(brand<string, "MessageTemplate">(value));
  });
}

export function translationCatalog(input: {
  readonly locale: LocaleTag;
  readonly messages: Readonly<Record<string, string | MessageTemplate>>;
}, diagnostics?: CoreI18nDiagnosticOptions): Result<TranslationCatalog, I18nError> {
  const observation = new I18nObservation("translation-catalog", diagnostics);
  return observation.run(() => {
  const messages: Record<string, MessageTemplate> = {};
  let ordinal = 0;
  observation.location("catalog-enumeration", "messages");
  for (const [key, value] of Object.entries(input.messages)) {
    observation.location("predicate-invocation", "catalog-key", ordinal);
    let reason: CoreI18nValidationDetail["reason"] = "empty";
    if (key.length === 0 || (reason = "contains-whitespace", /\s/.test(key))) {
      return err(
        observation.rejected(i18nError({
          code: "I18N_INVALID_TEMPLATE",
          defaultMessage: "Translation keys must be non-empty and must not contain whitespace.",
          messageKey: "i18n.translation_key.invalid",
          params: { key },
        }), { operation: "translation-catalog", field: "catalog-key", reason, ordinal }),
      );
    }

    observation.location("predicate-invocation", "template", ordinal);
    const template = messageTemplateAt(value, diagnostics, "translation-catalog", ordinal);

    if (!template.ok) {
      return template;
    }

    observation.location("catalog-copy", "messages", ordinal);
    messages[key] = template.value;
    ordinal++;
    observation.location("catalog-enumeration", "messages");
  }

  observation.location("result-projection", "locale");
  return ok({
    locale: input.locale,
    messages,
  });
  });
}

export function safeTranslationParams(
  params: MessageParams,
  options: TranslationParamOptions = {},
  diagnostics?: CoreI18nDiagnosticOptions,
): Result<MessageParams, I18nError> {
  const observation = new I18nObservation("translation-params", diagnostics);
  return observation.run(() => {
  observation.location("unsafe-name-declaration", "additional-unsafe-param-names");
  const unsafeParamNames = new Set(
    [...defaultUnsafeTranslationParamNames, ...(options.additionalUnsafeParamNames ?? [])].map(normalizeParamName),
  );

  let ordinal = 0;
  observation.location("parameter-enumeration", "params");
  for (const key of Object.keys(params)) {
    observation.location("predicate-invocation", "parameter", ordinal);
    if (unsafeParamNames.has(normalizeParamName(key))) {
      return err(observation.rejected(unsafeTemplateParamError(key), { operation: "translation-params", field: "parameter", reason: "unsafe-name", ordinal }));
    }
    ordinal++;
    observation.location("parameter-enumeration", "params");
  }

  observation.location("parameter-copy", "params");
  return ok({ ...params });
  });
}

export const defaultMessageTranslator: MessageTranslator = {
  translate: (message, request, diagnostics) => {
    const observation = new I18nObservation("translate", diagnostics);
    return observation.run(() => {
      observation.selection({ selection: "default-message", reason: "default-translator" });
      observation.location("input-projection", "locale");
      return translateDefaultMessage(message, request.locale, diagnostics, observation);
    });
  },
};

export function catalogMessageTranslator(catalogs: readonly TranslationCatalog[], diagnostics?: CoreI18nDiagnosticOptions): MessageTranslator {
  const construction = new I18nObservation("catalog-translator", diagnostics);
  return construction.run(() => {
  let catalogOrdinal = 0;
  construction.location("catalog-index", "catalogs");
  const catalogByLocale = new Map<string, TranslationCatalog>(
    construction.argument("catalog-index", "catalogs", construction.at("catalog-copy", "catalogs", () => catalogs.map((catalog) => {
      const ordinal = catalogOrdinal++;
      return construction.at("catalog-copy", "catalog", () => [
      construction.at("input-projection", "locale", () => catalog.locale, ordinal),
      {
        locale: construction.at("input-projection", "locale", () => catalog.locale, ordinal),
        messages: construction.at("catalog-copy", "messages", () => ({ ...catalog.messages }), ordinal),
      },
    ] as [LocaleTag, TranslationCatalog], ordinal);
    }))),
  );

  return {
    translate(message, request, invocationDiagnostics) {
      const selectedDiagnostics = invocationDiagnostics === undefined ? diagnostics : invocationDiagnostics;
      const observation = new I18nObservation("translate", selectedDiagnostics);
      return observation.run(() => {
      observation.location("candidate-iteration", "fallback-locales");
      const requestedLocales = [observation.at("input-projection", "locale", () => request.locale),
        ...(observation.at("input-projection", "fallback-locales", () => request.fallbackLocales) ?? [])];

      observation.location("input-projection", "message-key");
      const hasMessageKey = message.messageKey !== undefined;
      let ordinal = 0, catalogMisses = 0, templateMisses = 0;
      if (hasMessageKey) {
        observation.location("candidate-iteration", "fallback-locales");
        for (const requestedLocale of requestedLocales) {
          observation.location("catalog-lookup", "catalog", ordinal);
          const catalog = catalogByLocale.get(requestedLocale);
          observation.location("input-projection", "messages", ordinal);
          const template = catalog?.messages[observation.argument("template-lookup", "template",
            observation.at("input-projection", "message-key", () => message.messageKey as MessageKey, ordinal), ordinal)];

          if (template !== undefined) {
            observation.selection({ selection: ordinal === 0 ? "requested-catalog" : "fallback-catalog", reason: "candidate-present", ordinal, catalogMisses, templateMisses });
            observation.location("input-projection", "params", ordinal);
            const rendered = interpolateMessageTemplate(template,
              observation.argument("interpolation", "template", observation.at("input-projection", "params", () => message.params, ordinal), ordinal), selectedDiagnostics);

            if (!rendered.ok) {
              return rendered;
            }

            observation.location("result-projection");
            return ok({
              locale: requestedLocale,
              text: rendered.value,
              source: "catalog",
              messageKey: observation.at("result-projection", "message-key", () => message.messageKey as MessageKey),
              ...translatedParamKeys(observation.at("result-projection", "params", () => message.params), observation),
            });
          }
          if (catalog === undefined || catalog === null) catalogMisses++; else templateMisses++;
          ordinal++;
          observation.location("candidate-iteration", "fallback-locales");
        }
      }

      observation.selection({ selection: "default-message", reason: hasMessageKey ? "no-candidate-match" : "no-message-key", catalogMisses, templateMisses });
      observation.location("input-projection", "locale");
      return translateDefaultMessage(message, request.locale, selectedDiagnostics, observation);
      });
    },
  };
  });
}

export function interpolateMessageTemplate(
  template: string | MessageTemplate,
  params: MessageParams = {},
  diagnostics?: CoreI18nDiagnosticOptions,
): Result<string, I18nError> {
  const observation = new I18nObservation("interpolate", diagnostics);
  return observation.run(() => {
  observation.location("input-projection", "params");
  const safeParams = safeTranslationParams(params, undefined, diagnostics);

  if (!safeParams.ok) {
    return safeParams;
  }

  let missingParam: string | undefined;
  let ordinal = 0, missingOrdinal: number | undefined;
  observation.location("interpolation", "template");
  const rendered = template.replace(templateParamPattern, (match, rawParamName: string) => {
    const currentOrdinal = ordinal++;
    return observation.at("predicate-invocation", "parameter", () => {
    if (!Object.prototype.hasOwnProperty.call(safeParams.value, rawParamName)) {
      missingParam = rawParamName;
      missingOrdinal = currentOrdinal;
      return match;
    }

    return observation.at("parameter-coercion", "parameter", () => String(safeParams.value[rawParamName] as MessageParamValue), currentOrdinal);
    }, currentOrdinal);
  });

  if (missingParam !== undefined) {
    return err(observation.rejected(missingTemplateParamError(missingParam), { operation: "interpolate", field: "parameter", reason: "missing-own-property", ...(missingOrdinal === undefined ? {} : { ordinal: missingOrdinal }) }));
  }

  return ok(rendered);
  });
}

export function i18nError(input: {
  readonly code: I18nErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly details?: Readonly<Record<string, unknown>>;
}, diagnostics?: CoreI18nDiagnosticOptions): I18nError {
  const observation = new I18nObservation("error", diagnostics);
  return observation.run(() => {
  observation.location("error-projection");
  return {
    code: observation.at("error-projection", "code", () => input.code),
    defaultMessage: observation.at("error-projection", "default-message", () => input.defaultMessage),
    ...observation.at("error-projection", "message-key", () => input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...observation.at("error-projection", "params", () => input.params === undefined ? {} : { params: input.params }),
    ...observation.at("error-projection", "cause", () => input.cause === undefined ? {} : { cause: input.cause }),
    ...observation.at("error-projection", "diagnostic", () => input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...observation.at("error-projection", "diagnostic-record", () => input.diagnosticRecord === undefined ? {} : { diagnosticRecord: input.diagnosticRecord }),
    ...observation.at("error-projection", "details", () => input.details === undefined ? {} : { details: input.details }),
  };
  });
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

function translateDefaultMessage(message: MessageDescriptor, locale: LocaleTag, diagnostics: CoreI18nDiagnosticOptions | undefined, observation: I18nObservation): Result<TranslatedMessage, I18nError> {
  observation.location("input-projection", "default-message");
  const rendered = interpolateMessageTemplate(
    observation.at("input-projection", "default-message", () => message.defaultMessage),
    observation.argument("interpolation", "template", observation.at("input-projection", "params", () => message.params)), diagnostics);

  if (!rendered.ok) {
    return rendered;
  }

  observation.location("result-projection");
  return ok({
    locale,
    text: rendered.value,
    source: "default-message",
    ...observation.at("result-projection", "message-key", () => message.messageKey === undefined ? {} : { messageKey: message.messageKey }),
    ...translatedParamKeys(observation.at("result-projection", "params", () => message.params), observation),
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

function unsafeTemplateParamError(param: string): I18nError {
  return i18nError({
    code: "I18N_UNSAFE_TEMPLATE_PARAM",
    defaultMessage: "Message template parameter is not safe for translation output.",
    messageKey: "i18n.template_param.unsafe",
    params: { param },
  });
}

function translatedParamKeys(params: MessageParams | undefined, observation: I18nObservation): { readonly paramKeys?: readonly string[] } {
  if (params === undefined) {
    return {};
  }

  return {
    paramKeys: observation.at("parameter-enumeration", "params", () => Object.keys(params)),
  };
}

function normalizeParamName(value: string): string {
  return value.replace(/[^A-Za-z0-9]/g, "").toLowerCase();
}
