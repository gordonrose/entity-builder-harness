import { localeTag, type LocaleTag } from "../src/i18n/index";
import {
  currencyCode,
  fixedLocalizer,
  localizableCurrency,
  localizableDateTime,
  localizableNumber,
  localizableRegion,
  localizationError,
  regionCode,
  timeZoneId,
  unsupportedLocalizer,
  type CurrencyCode,
  type LocalizableCurrency,
  type LocalizableDateTime,
  type LocalizableNumber,
  type LocalizableRegion,
  type LocalizableValue,
  type LocalizationError,
  type LocalizationErrorCode,
  type LocalizationRequest,
  type LocalizedFormat,
  type Localizer,
  type RegionCode,
  type TimeZoneId,
} from "../src/localization/index";
import { isOk, isoDateTime, type Result } from "../src/shared/index";

const localeResult = localeTag("en-GB");
if (!isOk(localeResult)) {
  throw new Error("Expected locale to be valid.");
}
const locale: LocaleTag = localeResult.value;

const currencyResult = currencyCode("GBP");
if (!isOk(currencyResult)) {
  throw new Error("Expected currency to be valid.");
}
const currency: CurrencyCode = currencyResult.value;

const regionResult = regionCode("GB");
if (!isOk(regionResult)) {
  throw new Error("Expected region to be valid.");
}
const region: RegionCode = regionResult.value;

const timeZoneResult = timeZoneId("Europe/London");
if (!isOk(timeZoneResult)) {
  throw new Error("Expected time zone to be valid.");
}
const timeZone: TimeZoneId = timeZoneResult.value;

const nowResult = isoDateTime("2026-07-08T12:34:56Z");
if (!isOk(nowResult)) {
  throw new Error("Expected date-time to be valid.");
}

const dateTimeValue: LocalizableDateTime = localizableDateTime({
  value: nowResult.value,
  dateStyle: "short",
  timeZone,
});
const numberResult: Result<LocalizableNumber, LocalizationError> = localizableNumber({ value: 42 });
if (!isOk(numberResult)) {
  throw new Error("Expected number to be valid.");
}
const currencyValueResult: Result<LocalizableCurrency, LocalizationError> = localizableCurrency({
  amount: 19.99,
  currency,
});
if (!isOk(currencyValueResult)) {
  throw new Error("Expected currency value to be valid.");
}
const regionValue: LocalizableRegion = localizableRegion(region);
const value: LocalizableValue = dateTimeValue;
const request: LocalizationRequest = {
  locale,
  value,
};
const localizer: Localizer = fixedLocalizer("8 July 2026");
const formatted: Result<LocalizedFormat, LocalizationError> = localizer.format(request);
void formatted;
void numberResult;
void currencyValueResult;
void regionValue;

const failingLocalizer: Localizer = unsupportedLocalizer();
void failingLocalizer;

const errorCode: LocalizationErrorCode = "LOCALIZATION_UNSUPPORTED_FORMAT";
const explicitError: LocalizationError = localizationError({
  code: errorCode,
  defaultMessage: "Unsupported format.",
});
void explicitError;

// @ts-expect-error currency codes must be explicitly branded.
const invalidCurrency: CurrencyCode = "GBP";
void invalidCurrency;

// @ts-expect-error region codes must be explicitly branded.
const invalidRegion: RegionCode = "GB";
void invalidRegion;

// @ts-expect-error time zone ids must be explicitly branded.
const invalidTimeZone: TimeZoneId = "Europe/London";
void invalidTimeZone;

// @ts-expect-error localization requests require branded locale tags.
const invalidRequest: LocalizationRequest = { locale: "en-GB", value };
void invalidRequest;

// @ts-expect-error localizable date-time values require ISODateTime values.
localizableDateTime({ value: "2026-07-08T12:34:56Z" });

// @ts-expect-error currency localizable values require branded currency codes.
localizableCurrency({ amount: 19.99, currency: "GBP" });

// @ts-expect-error localization error codes are constrained.
localizationError({ code: "LOCALIZATION_BROKEN", defaultMessage: "Broken." });
