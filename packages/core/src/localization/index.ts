import {
  brand,
  err,
  messageKey,
  ok,
  type Brand,
  type CoreError,
  type ISODateTime,
  type MessageKey,
  type MessageParams,
  type Result,
} from "../shared/index";
import type { DiagnosticDescriptor } from "../diagnostics/index";
import type { LocaleTag } from "../i18n/index";

export type CurrencyCode = Brand<string, "CurrencyCode">;
export type RegionCode = Brand<string, "RegionCode">;
export type TimeZoneId = Brand<string, "TimeZoneId">;

export type LocalizationErrorCode =
  | "LOCALIZATION_INVALID_CURRENCY"
  | "LOCALIZATION_INVALID_NUMBER"
  | "LOCALIZATION_INVALID_REGION"
  | "LOCALIZATION_INVALID_TIME_ZONE"
  | "LOCALIZATION_UNSUPPORTED_FORMAT";

export interface LocalizationError extends CoreError {
  readonly code: LocalizationErrorCode;
}

export const localizedValueKinds = ["date-time", "number", "currency", "region"] as const;
export type LocalizedValueKind = (typeof localizedValueKinds)[number];

export const localizedDateTimeStyles = ["full", "long", "medium", "short"] as const;
export type LocalizedDateTimeStyle = (typeof localizedDateTimeStyles)[number];

export interface LocalizableDateTime {
  readonly kind: "date-time";
  readonly value: ISODateTime;
  readonly dateStyle?: LocalizedDateTimeStyle;
  readonly timeStyle?: LocalizedDateTimeStyle;
  readonly timeZone?: TimeZoneId;
}

export interface LocalizableNumber {
  readonly kind: "number";
  readonly value: number;
  readonly minimumFractionDigits?: number;
  readonly maximumFractionDigits?: number;
}

export interface LocalizableCurrency {
  readonly kind: "currency";
  readonly amount: number;
  readonly currency: CurrencyCode;
  readonly minimumFractionDigits?: number;
  readonly maximumFractionDigits?: number;
}

export interface LocalizableRegion {
  readonly kind: "region";
  readonly region: RegionCode;
}

export type LocalizableValue =
  | LocalizableDateTime
  | LocalizableNumber
  | LocalizableCurrency
  | LocalizableRegion;

export interface LocalizationRequest<TValue extends LocalizableValue = LocalizableValue> {
  readonly locale: LocaleTag;
  readonly value: TValue;
}

export interface LocalizedFormat {
  readonly locale: LocaleTag;
  readonly kind: LocalizedValueKind;
  readonly text: string;
}

export interface Localizer {
  format<TValue extends LocalizableValue>(
    request: LocalizationRequest<TValue>,
  ): Result<LocalizedFormat, LocalizationError>;
}

export function currencyCode(value: string): Result<CurrencyCode, LocalizationError> {
  if (!/^[A-Za-z]{3}$/.test(value)) {
    return err(
      localizationError({
        code: "LOCALIZATION_INVALID_CURRENCY",
        defaultMessage: "Currency code must be a three-letter ISO 4217 code.",
        messageKey: "localization.currency.invalid",
        params: { currency: value },
      }),
    );
  }

  return ok(brand<string, "CurrencyCode">(value.toUpperCase()));
}

export function regionCode(value: string): Result<RegionCode, LocalizationError> {
  if (!/^(?:[A-Za-z]{2}|\d{3})$/.test(value)) {
    return err(
      localizationError({
        code: "LOCALIZATION_INVALID_REGION",
        defaultMessage: "Region code must be a two-letter or three-digit region code.",
        messageKey: "localization.region.invalid",
        params: { region: value },
      }),
    );
  }

  return ok(brand<string, "RegionCode">(value.toUpperCase()));
}

export function timeZoneId(value: string): Result<TimeZoneId, LocalizationError> {
  if (value.length === 0 || /\s/.test(value)) {
    return err(
      localizationError({
        code: "LOCALIZATION_INVALID_TIME_ZONE",
        defaultMessage: "Time zone id must be non-empty and must not contain whitespace.",
        messageKey: "localization.time_zone.invalid",
        params: { timeZone: value },
      }),
    );
  }

  return ok(brand<string, "TimeZoneId">(value));
}

export function localizableDateTime(input: {
  readonly value: ISODateTime;
  readonly dateStyle?: LocalizedDateTimeStyle;
  readonly timeStyle?: LocalizedDateTimeStyle;
  readonly timeZone?: TimeZoneId;
}): LocalizableDateTime {
  return {
    kind: "date-time",
    value: input.value,
    ...(input.dateStyle === undefined ? {} : { dateStyle: input.dateStyle }),
    ...(input.timeStyle === undefined ? {} : { timeStyle: input.timeStyle }),
    ...(input.timeZone === undefined ? {} : { timeZone: input.timeZone }),
  };
}

export function localizableNumber(input: {
  readonly value: number;
  readonly minimumFractionDigits?: number;
  readonly maximumFractionDigits?: number;
}): Result<LocalizableNumber, LocalizationError> {
  const fractionDigits = validateFractionDigits(input.minimumFractionDigits, input.maximumFractionDigits);

  if (!Number.isFinite(input.value)) {
    return err(invalidNumberError("value", input.value));
  }

  if (!fractionDigits.ok) {
    return fractionDigits;
  }

  return ok({
    kind: "number",
    value: input.value,
    ...(input.minimumFractionDigits === undefined ? {} : { minimumFractionDigits: input.minimumFractionDigits }),
    ...(input.maximumFractionDigits === undefined ? {} : { maximumFractionDigits: input.maximumFractionDigits }),
  });
}

export function localizableCurrency(input: {
  readonly amount: number;
  readonly currency: CurrencyCode;
  readonly minimumFractionDigits?: number;
  readonly maximumFractionDigits?: number;
}): Result<LocalizableCurrency, LocalizationError> {
  const fractionDigits = validateFractionDigits(input.minimumFractionDigits, input.maximumFractionDigits);

  if (!Number.isFinite(input.amount)) {
    return err(invalidNumberError("amount", input.amount));
  }

  if (!fractionDigits.ok) {
    return fractionDigits;
  }

  return ok({
    kind: "currency",
    amount: input.amount,
    currency: input.currency,
    ...(input.minimumFractionDigits === undefined ? {} : { minimumFractionDigits: input.minimumFractionDigits }),
    ...(input.maximumFractionDigits === undefined ? {} : { maximumFractionDigits: input.maximumFractionDigits }),
  });
}

export function localizableRegion(region: RegionCode): LocalizableRegion {
  return {
    kind: "region",
    region,
  };
}

export function localizedFormat(input: {
  readonly locale: LocaleTag;
  readonly kind: LocalizedValueKind;
  readonly text: string;
}): LocalizedFormat {
  return {
    locale: input.locale,
    kind: input.kind,
    text: input.text,
  };
}

export function fixedLocalizer(text: string): Localizer {
  return {
    format: (request) =>
      ok(
        localizedFormat({
          locale: request.locale,
          kind: request.value.kind,
          text,
        }),
      ),
  };
}

export function unsupportedLocalizer(reason: {
  readonly defaultMessage?: string;
  readonly messageKey?: string | MessageKey;
} = {}): Localizer {
  return {
    format: () =>
      err(
        localizationError({
          code: "LOCALIZATION_UNSUPPORTED_FORMAT",
          defaultMessage: reason.defaultMessage ?? "Localized formatting is not supported.",
          ...(reason.messageKey === undefined ? {} : { messageKey: reason.messageKey }),
        }),
      ),
  };
}

export function localizationError(input: {
  readonly code: LocalizationErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly details?: Readonly<Record<string, unknown>>;
}): LocalizationError {
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

function validateFractionDigits(
  minimumFractionDigits: number | undefined,
  maximumFractionDigits: number | undefined,
): Result<void, LocalizationError> {
  if (minimumFractionDigits !== undefined && !isNonNegativeInteger(minimumFractionDigits)) {
    return err(invalidNumberError("minimumFractionDigits", minimumFractionDigits));
  }

  if (maximumFractionDigits !== undefined && !isNonNegativeInteger(maximumFractionDigits)) {
    return err(invalidNumberError("maximumFractionDigits", maximumFractionDigits));
  }

  if (
    minimumFractionDigits !== undefined &&
    maximumFractionDigits !== undefined &&
    minimumFractionDigits > maximumFractionDigits
  ) {
    return err(
      localizationError({
        code: "LOCALIZATION_INVALID_NUMBER",
        defaultMessage: "Minimum fraction digits must be less than or equal to maximum fraction digits.",
        messageKey: "localization.number.fraction_digits.invalid",
        params: {
          minimumFractionDigits,
          maximumFractionDigits,
        },
      }),
    );
  }

  return ok(undefined);
}

function invalidNumberError(field: string, value: number): LocalizationError {
  return localizationError({
    code: "LOCALIZATION_INVALID_NUMBER",
    defaultMessage: "Localized number values must be finite.",
    messageKey: "localization.number.invalid",
    params: { field, value: String(value) },
  });
}

function isNonNegativeInteger(value: number): boolean {
  return Number.isInteger(value) && value >= 0;
}
