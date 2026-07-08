import { deepEqual, equal } from "node:assert/strict";
import { diagnosticDescriptor } from "../src/diagnostics/index";
import { localeTag } from "../src/i18n/index";
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
} from "../src/localization/index";
import { isErr, isOk, isoDateTime } from "../src/shared/index";

const locale = localeTag("en-gb");
equal(isOk(locale), true);
if (!isOk(locale)) {
  throw new Error("Expected en-gb to be valid.");
}

const currency = currencyCode("usd");
equal(isOk(currency), true);
if (!isOk(currency)) {
  throw new Error("Expected usd to be a valid currency code.");
}
equal(currency.value, "USD");

const invalidCurrency = currencyCode("US");
equal(isErr(invalidCurrency), true);
if (!isErr(invalidCurrency)) {
  throw new Error("Expected invalid currency to fail.");
}
equal(invalidCurrency.error.code, "LOCALIZATION_INVALID_CURRENCY");

const region = regionCode("gb");
equal(isOk(region), true);
if (!isOk(region)) {
  throw new Error("Expected gb to be a valid region code.");
}
equal(region.value, "GB");

const macroRegion = regionCode("419");
equal(isOk(macroRegion), true);
if (!isOk(macroRegion)) {
  throw new Error("Expected 419 to be a valid numeric region code.");
}
equal(macroRegion.value, "419");

const timeZone = timeZoneId("Europe/London");
equal(isOk(timeZone), true);
if (!isOk(timeZone)) {
  throw new Error("Expected Europe/London to be a valid time zone id.");
}

const utcTimeZone = timeZoneId("UTC");
equal(isOk(utcTimeZone), true);
if (!isOk(utcTimeZone)) {
  throw new Error("Expected UTC to be a valid time zone id.");
}

const invalidTimeZone = timeZoneId("Europe London");
equal(isErr(invalidTimeZone), true);
if (!isErr(invalidTimeZone)) {
  throw new Error("Expected invalid time zone to fail.");
}
equal(invalidTimeZone.error.code, "LOCALIZATION_INVALID_TIME_ZONE");

const pathLikeTimeZone = timeZoneId("../Europe/London");
equal(isErr(pathLikeTimeZone), true);
if (!isErr(pathLikeTimeZone)) {
  throw new Error("Expected path-like time zone to fail.");
}
equal(pathLikeTimeZone.error.code, "LOCALIZATION_INVALID_TIME_ZONE");

const markupLikeTimeZone = timeZoneId("<Europe/London>");
equal(isErr(markupLikeTimeZone), true);
if (!isErr(markupLikeTimeZone)) {
  throw new Error("Expected markup-like time zone to fail.");
}
equal(markupLikeTimeZone.error.code, "LOCALIZATION_INVALID_TIME_ZONE");

const now = isoDateTime("2026-07-08T12:34:56Z");
equal(isOk(now), true);
if (!isOk(now)) {
  throw new Error("Expected ISO date-time to be valid.");
}
deepEqual(
  localizableDateTime({
    value: now.value,
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: timeZone.value,
  }),
  {
    kind: "date-time",
    value: "2026-07-08T12:34:56.000Z",
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Europe/London",
  },
);

const numberValue = localizableNumber({
  value: 1234.5,
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});
equal(isOk(numberValue), true);
if (!isOk(numberValue)) {
  throw new Error("Expected localizable number to be valid.");
}
deepEqual(numberValue.value, {
  kind: "number",
  value: 1234.5,
  minimumFractionDigits: 0,
  maximumFractionDigits: 2,
});

const invalidNumber = localizableNumber({ value: Number.NaN });
equal(isErr(invalidNumber), true);
if (!isErr(invalidNumber)) {
  throw new Error("Expected invalid number to fail.");
}
equal(invalidNumber.error.code, "LOCALIZATION_INVALID_NUMBER");

const invalidFractionDigits = localizableNumber({
  value: 42,
  minimumFractionDigits: 3,
  maximumFractionDigits: 2,
});
equal(isErr(invalidFractionDigits), true);
if (!isErr(invalidFractionDigits)) {
  throw new Error("Expected invalid fraction digits to fail.");
}
equal(invalidFractionDigits.error.code, "LOCALIZATION_INVALID_NUMBER");

const money = localizableCurrency({
  amount: 19.99,
  currency: currency.value,
});
equal(isOk(money), true);
if (!isOk(money)) {
  throw new Error("Expected localizable currency to be valid.");
}
deepEqual(money.value, {
  kind: "currency",
  amount: 19.99,
  currency: "USD",
});

deepEqual(localizableRegion(region.value), {
  kind: "region",
  region: "GB",
});

const localizer = fixedLocalizer("8 July 2026");
const formatted = localizer.format({
  locale: locale.value,
  value: localizableDateTime({ value: now.value }),
});
equal(isOk(formatted), true);
if (!isOk(formatted)) {
  throw new Error("Expected fixed localizer to succeed.");
}
deepEqual(formatted.value, {
  locale: "en-GB",
  kind: "date-time",
  text: "8 July 2026",
});

const unsupported = unsupportedLocalizer().format({
  locale: locale.value,
  value: numberValue.value,
});
equal(isErr(unsupported), true);
if (!isErr(unsupported)) {
  throw new Error("Expected unsupported localizer to fail.");
}
equal(unsupported.error.code, "LOCALIZATION_UNSUPPORTED_FORMAT");

const diagnostic = diagnosticDescriptor({
  failureKind: "validation",
  failureSource: "app",
  severity: "warning",
  recovery: "user_correctable",
});
const explicitError = localizationError({
  code: "LOCALIZATION_UNSUPPORTED_FORMAT",
  defaultMessage: "Format is unsupported.",
  diagnostic,
});
equal(explicitError.diagnostic, diagnostic);

console.log("packages/core localization runtime test passed.");
