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
import { LocalizationObservation } from "./observations";
import type { CoreLocalizationDiagnosticOptions } from "./diagnostics";
export * from "./diagnostics";
export { observeCoreLocalizationDiagnostic, selectCoreLocalizationDiagnosticEvidence } from "./observations";

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
    diagnostics?: CoreLocalizationDiagnosticOptions,
  ): Result<LocalizedFormat, LocalizationError>;
}

export function currencyCode(value: string, diagnostics?: CoreLocalizationDiagnosticOptions): Result<CurrencyCode, LocalizationError> {
  const o = new LocalizationObservation("currency-code", diagnostics);
  return o.run(() => {
  if (o.rejects("currency", "invalid-format", () => !/^[A-Za-z]{3}$/.test(value))) {
    return err(
      o.attach(ownedLocalizationError({
        code: "LOCALIZATION_INVALID_CURRENCY",
        defaultMessage: "Currency code must be a three-letter ISO 4217 code.",
        messageKey: "localization.currency.invalid",
        params: { currency: value },
      }, o)),
    );
  }

  return ok(brand<string, "CurrencyCode">(o.at("normalization", "currency", () => value.toUpperCase())));
  });
}

export function regionCode(value: string, diagnostics?: CoreLocalizationDiagnosticOptions): Result<RegionCode, LocalizationError> {
  const o = new LocalizationObservation("region-code", diagnostics);
  return o.run(() => {
  if (o.rejects("region", "invalid-format", () => !/^(?:[A-Za-z]{2}|\d{3})$/.test(value))) {
    return err(
      o.attach(ownedLocalizationError({
        code: "LOCALIZATION_INVALID_REGION",
        defaultMessage: "Region code must be a two-letter or three-digit region code.",
        messageKey: "localization.region.invalid",
        params: { region: value },
      }, o)),
    );
  }

  return ok(brand<string, "RegionCode">(o.at("normalization", "region", () => value.toUpperCase())));
  });
}

export function timeZoneId(value: string, diagnostics?: CoreLocalizationDiagnosticOptions): Result<TimeZoneId, LocalizationError> {
  const o = new LocalizationObservation("time-zone-id", diagnostics);
  return o.run(() => {
  if (o.rejects("time-zone", "invalid-format", () => !timeZoneIdPattern.test(value)) || o.rejects("time-zone", "parent-sequence-rejected", () => value.includes(".."))) {
    return err(
      o.attach(ownedLocalizationError({
        code: "LOCALIZATION_INVALID_TIME_ZONE",
        defaultMessage: "Time zone id must be UTC or an IANA-style slash-separated identifier.",
        messageKey: "localization.time_zone.invalid",
        params: { timeZone: value },
      }, o)),
    );
  }

  return ok(brand<string, "TimeZoneId">(value));
  });
}

export function localizableDateTime(input: {
  readonly value: ISODateTime;
  readonly dateStyle?: LocalizedDateTimeStyle;
  readonly timeStyle?: LocalizedDateTimeStyle;
  readonly timeZone?: TimeZoneId;
}, diagnostics?: CoreLocalizationDiagnosticOptions): LocalizableDateTime {
  const o = new LocalizationObservation("date-time", diagnostics);
  return o.run(() => {
  return o.at("result-projection", undefined, () => ({
    kind: "date-time",
    value: o.read("value", () => input.value)!,
    ...(o.read("date-style", () => input.dateStyle)! === undefined ? {} : { dateStyle: o.read("date-style", () => input.dateStyle)! }),
    ...(o.read("time-style", () => input.timeStyle)! === undefined ? {} : { timeStyle: o.read("time-style", () => input.timeStyle)! }),
    ...(o.read("time-zone", () => input.timeZone)! === undefined ? {} : { timeZone: o.read("time-zone", () => input.timeZone)! }),
  }));
  });
}

export function localizableNumber(input: {
  readonly value: number;
  readonly minimumFractionDigits?: number;
  readonly maximumFractionDigits?: number;
}, diagnostics?: CoreLocalizationDiagnosticOptions): Result<LocalizableNumber, LocalizationError> {
  const o = new LocalizationObservation("number", diagnostics);
  return o.run(() => {
  const fractionDigits = validateFractionDigits(o.read("minimum-fraction-digits", () => input.minimumFractionDigits)!, o.read("maximum-fraction-digits", () => input.maximumFractionDigits)!, o);

  if (o.rejects("value", "not-finite", () => !Number.isFinite(o.read("value", () => input.value)!))) {
    return err(o.attach(invalidNumberError("value", o.read("value", () => input.value)!, "value", o)));
  }

  if (!fractionDigits.ok) {
    return fractionDigits;
  }

  return ok(o.at("result-projection", undefined, () => ({
    kind: "number",
    value: o.read("value", () => input.value)!,
    ...(o.read("minimum-fraction-digits", () => input.minimumFractionDigits)! === undefined ? {} : { minimumFractionDigits: o.read("minimum-fraction-digits", () => input.minimumFractionDigits)! }),
    ...(o.read("maximum-fraction-digits", () => input.maximumFractionDigits)! === undefined ? {} : { maximumFractionDigits: o.read("maximum-fraction-digits", () => input.maximumFractionDigits)! }),
  })));
  });
}

export function localizableCurrency(input: {
  readonly amount: number;
  readonly currency: CurrencyCode;
  readonly minimumFractionDigits?: number;
  readonly maximumFractionDigits?: number;
}, diagnostics?: CoreLocalizationDiagnosticOptions): Result<LocalizableCurrency, LocalizationError> {
  const o = new LocalizationObservation("currency", diagnostics);
  return o.run(() => {
  const fractionDigits = validateFractionDigits(o.read("minimum-fraction-digits", () => input.minimumFractionDigits)!, o.read("maximum-fraction-digits", () => input.maximumFractionDigits)!, o);

  if (o.rejects("amount", "not-finite", () => !Number.isFinite(o.read("amount", () => input.amount)!))) {
    return err(o.attach(invalidNumberError("amount", o.read("amount", () => input.amount)!, "amount", o)));
  }

  if (!fractionDigits.ok) {
    return fractionDigits;
  }

  return ok(o.at("result-projection", undefined, () => ({
    kind: "currency",
    amount: o.read("amount", () => input.amount)!,
    currency: o.read("currency", () => input.currency)!,
    ...(o.read("minimum-fraction-digits", () => input.minimumFractionDigits)! === undefined ? {} : { minimumFractionDigits: o.read("minimum-fraction-digits", () => input.minimumFractionDigits)! }),
    ...(o.read("maximum-fraction-digits", () => input.maximumFractionDigits)! === undefined ? {} : { maximumFractionDigits: o.read("maximum-fraction-digits", () => input.maximumFractionDigits)! }),
  })));
  });
}

export function localizableRegion(region: RegionCode, diagnostics?: CoreLocalizationDiagnosticOptions): LocalizableRegion {
  const o = new LocalizationObservation("region", diagnostics);
  return o.run(() => {
  return o.at("result-projection", undefined, () => ({
    kind: "region",
    region,
  }));
  });
}

export function localizedFormat(input: {
  readonly locale: LocaleTag;
  readonly kind: LocalizedValueKind;
  readonly text: string;
}, diagnostics?: CoreLocalizationDiagnosticOptions): LocalizedFormat {
  const o = new LocalizationObservation("localized-format", diagnostics);
  return o.run(() => ownedLocalizedFormat(input, o));
}

function ownedLocalizedFormat(input: LocalizedFormat, o: LocalizationObservation): LocalizedFormat {
  return o.at("result-projection", undefined, () => ({
    locale: o.read("locale", () => input.locale)!,
    kind: o.read("kind", () => input.kind)!,
    text: o.read("text", () => input.text)!,
  }));
}

export function fixedLocalizer(text: string, diagnostics?: CoreLocalizationDiagnosticOptions): Localizer {
  return {
    format: (request, invocationDiagnostics) => {
      const o = new LocalizationObservation("format", invocationDiagnostics === undefined ? diagnostics : invocationDiagnostics);
      return o.run(() => ok(
        ownedLocalizedFormat({
          locale: o.read("locale", () => request.locale),
          kind: o.read("kind", () => o.read("value", () => request.value).kind),
          text,
        }, o),
      ));
    },
  };
}

export function unsupportedLocalizer(reason: {
  readonly defaultMessage?: string;
  readonly messageKey?: string | MessageKey;
} = {}, diagnostics?: CoreLocalizationDiagnosticOptions): Localizer {
  return {
    format: (_request, invocationDiagnostics) => {
      const o = new LocalizationObservation("format", invocationDiagnostics === undefined ? diagnostics : invocationDiagnostics);
      return o.run(() => {
      const unsupported = o.unsupported();
      return err(Object.assign(
        ownedLocalizationError({
          code: "LOCALIZATION_UNSUPPORTED_FORMAT",
          defaultMessage: o.at("reason-projection", "default-message", () => reason.defaultMessage) ?? "Localized formatting is not supported.",
          ...(o.at("reason-projection", "message-key", () => reason.messageKey) === undefined ? {} : { messageKey: o.at("reason-projection", "message-key", () => reason.messageKey)! }),
        }, o), { diagnosticRecord: unsupported }));
      });
    },
  };
}

export function localizationError(input: {
  readonly code: LocalizationErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly details?: Readonly<Record<string, unknown>>;
}, diagnostics?: CoreLocalizationDiagnosticOptions): LocalizationError {
  const o = new LocalizationObservation("error", diagnostics);
  return o.run(() => ownedLocalizationError(input, o));
}

function ownedLocalizationError(input: Parameters<typeof localizationError>[0], o: LocalizationObservation): LocalizationError {
  return o.at("error-projection", undefined, () => copyLocalizationError(input, o));
}

function copyLocalizationError(input: Parameters<typeof localizationError>[0], o: LocalizationObservation): LocalizationError {
  return {
    code: o.read("code", () => input.code)!,
    defaultMessage: o.read("default-message", () => input.defaultMessage)!,
    ...(o.read("message-key", () => input.messageKey)! === undefined ? {} : { messageKey: messageKey(o.read("message-key", () => input.messageKey)!) }),
    ...(o.read("params", () => input.params)! === undefined ? {} : { params: o.read("params", () => input.params)! }),
    ...(o.read("cause", () => input.cause)! === undefined ? {} : { cause: o.read("cause", () => input.cause)! }),
    ...(o.read("diagnostic", () => input.diagnostic)! === undefined ? {} : { diagnostic: o.read("diagnostic", () => input.diagnostic)! }),
    ...(o.read("diagnostic-record", () => input.diagnosticRecord)! === undefined ? {} : { diagnosticRecord: o.read("diagnostic-record", () => input.diagnosticRecord)! }),
    ...(o.read("details", () => input.details)! === undefined ? {} : { details: o.read("details", () => input.details)! }),
  };
}

function validateFractionDigits(
  minimumFractionDigits: number | undefined,
  maximumFractionDigits: number | undefined,
  o: LocalizationObservation,
): Result<void, LocalizationError> {
  if (minimumFractionDigits !== undefined && !isNonNegativeInteger(minimumFractionDigits, "minimum-fraction-digits", o)) {
    return err(o.attach(invalidNumberError("minimumFractionDigits", minimumFractionDigits, "minimum-fraction-digits", o)));
  }

  if (maximumFractionDigits !== undefined && !isNonNegativeInteger(maximumFractionDigits, "maximum-fraction-digits", o)) {
    return err(o.attach(invalidNumberError("maximumFractionDigits", maximumFractionDigits, "maximum-fraction-digits", o)));
  }

  if (
    minimumFractionDigits !== undefined &&
    maximumFractionDigits !== undefined &&
    o.rejects("fraction-range", "minimum-exceeds-maximum", () => minimumFractionDigits > maximumFractionDigits)
  ) {
    return err(o.attach(
      ownedLocalizationError({
        code: "LOCALIZATION_INVALID_NUMBER",
        defaultMessage: "Minimum fraction digits must be less than or equal to maximum fraction digits.",
        messageKey: "localization.number.fraction_digits.invalid",
        params: {
          minimumFractionDigits,
          maximumFractionDigits,
        },
      }, o),
    ));
  }

  return ok(undefined);
}

function invalidNumberError(field: string, value: number, logicalField: "value" | "amount" | "minimum-fraction-digits" | "maximum-fraction-digits", o: LocalizationObservation): LocalizationError {
  return ownedLocalizationError({
    code: "LOCALIZATION_INVALID_NUMBER",
    defaultMessage: "Localized number values must be finite.",
    messageKey: "localization.number.invalid",
    params: { field, value: o.at("parameter-formatting", logicalField, () => String(value)) },
  }, o);
}

function isNonNegativeInteger(value: number, field: "minimum-fraction-digits" | "maximum-fraction-digits", o: LocalizationObservation): boolean {
  return o.passes(field, "not-integer", () => Number.isInteger(value)) && o.passes(field, "negative", () => value >= 0);
}

const timeZoneIdPattern = /^(?:UTC|[A-Za-z][A-Za-z0-9_+-]*(?:\/[A-Za-z0-9_+-]+)+)$/;
