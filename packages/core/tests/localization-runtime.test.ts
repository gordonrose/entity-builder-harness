import { deepEqual, equal, throws } from "node:assert/strict";
import { diagnosticDescriptor, createDiagnosticRecord, defineDiagnostic, parseDiagnosticRecord, type DiagnosticRecord } from "../src/diagnostics/index";
import { localeTag } from "../src/i18n/index";
import {
  currencyCode,
  localizedFormat,
  coreLocalizationDiagnosticDefinitions,
  coreLocalizationBoundaryDiagnosticRecord,
  observeCoreLocalizationDiagnostic,
  type CoreLocalizationDiagnosticOptions,
  type CoreLocalizationDiagnosticContext,
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


const localeValue = locale.value, currencyValue = currency.value, dateValue = now.value;
const localizationRecord = (kind: string, detail: unknown) => ({
  schema: "core/diagnostic-record/v1", code: "core.localization." + kind, definitionVersion: 1, detail,
});
async function localizationDiagnosticProof(): Promise<void> {
  type NumberInput = Parameters<typeof localizableNumber>[0];
  type CurrencyInput = Parameters<typeof localizableCurrency>[0];
  const records: DiagnosticRecord[] = [];
  const contexts: CoreLocalizationDiagnosticContext[] = [];
  const diagnostics: CoreLocalizationDiagnosticOptions = {
    onDiagnostic(this: unknown, record, context) {
      equal(this, diagnostics);
      records.push(record); contexts.push(context);
    },
  };
  const reset = () => { records.length = 0; contexts.length = 0; };
  const validation = (operation: string, field: string, reason: string) =>
    localizationRecord("validation-rejected", { operation, field, reason, effect: "predicate-rejected" });
  const boundary = (operation: string, phase: string, field: string) =>
    localizationRecord("boundary-failed", { operation, phase, field, reason: "threw", effect: "value-not-produced" });
  const unsupported = localizationRecord("unsupported-observed", { operation: "format", phase: "implementation-selection", reason: "unsupported-implementation", effect: "format-not-performed" });
  for (const [run, operation, field] of [
    [() => currencyCode("US", diagnostics), "currency-code", "currency"],
    [() => regionCode("ABCD", diagnostics), "region-code", "region"],
    [() => timeZoneId("../Europe/London", diagnostics), "time-zone-id", "time-zone"],
  ] as const) {
    reset(); const result = run(); equal(result.ok, false);
    if (result.ok) throw new Error("Expected syntax rejection");
    deepEqual(records, [validation(operation, field, "invalid-format")]);
    deepEqual(result.error.diagnosticRecord, records[0]);
  }
  let coercions = 0, includeSelections = 0, includeCalls = 0;
  const customTimeZone = {
    toString() { coercions++; return "Europe/London"; },
    get includes() { includeSelections++; return function(this: unknown, argument: unknown) {
      equal(this, customTimeZone); equal(argument, ".."); includeCalls++; return "truthy" as never;
    }; },
  };
  reset();
  const parentSequence = timeZoneId(customTimeZone as never, diagnostics);
  equal(parentSequence.ok, false);
  deepEqual(records, [validation("time-zone-id", "time-zone", "parent-sequence-rejected")]);
  equal(coercions, 1); equal(includeSelections, 1); equal(includeCalls, 1);
  reset();
  const regexFirst = {
    toString() { return "../bad"; },
    get includes(): never { throw new Error("must not select includes"); },
  };
  equal(timeZoneId(regexFirst as never, diagnostics).ok, false);
  deepEqual(records, [validation("time-zone-id", "time-zone", "invalid-format")]);
  // Syntax-only policy: no ISO/Intl existence lookup or formatter bounds.
  reset();
  equal(currencyCode("ZZZ", diagnostics).ok, true);
  equal(regionCode("ZZ", diagnostics).ok, true);
  equal(timeZoneId("Mars/Unknown", diagnostics).ok, true);
  equal(localizableNumber({ value: -0, minimumFractionDigits: -0, maximumFractionDigits: 200 }, diagnostics).ok, true);
  equal(localizableCurrency({ currency: currencyValue, amount: -0, minimumFractionDigits: 200, maximumFractionDigits: 300 }, diagnostics).ok, true);
  equal(records.length, 0);

  const sourceDefinition = defineDiagnostic({
    code: "fixture.localization.source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
  } as const);
  const source9 = Array.from({ length: 9 }, (_, ordinal) => {
    const result = createDiagnosticRecord(sourceDefinition, { ordinal });
    if (!result.ok) throw new Error("Invalid source fixture");
    return result.value;
  });
  const raw = Object.freeze({ diagnosticRecord: source9[0], relatedDiagnosticRecords: source9.slice(1), private: "LOCALIZATION-PRIVATE-CANARY" });
  const selectedDiagnostics: CoreLocalizationDiagnosticOptions = {
    diagnosticDefinitions: [sourceDefinition],
    onDiagnostic(record, context) { records.push(record); contexts.push(context); },
  };
  for (const operation of ["number", "currency"] as const) {
    const valueField = operation === "number" ? "value" : "amount";
    const run = (minimumFractionDigits: number | undefined, maximumFractionDigits: number | undefined, value: number, options = diagnostics) =>
      operation === "number" ? localizableNumber({ minimumFractionDigits, maximumFractionDigits, value } as NumberInput, options) :
        localizableCurrency({ minimumFractionDigits, maximumFractionDigits, amount: value, currency: currencyValue } as CurrencyInput, options);
    for (const [minimum, maximum, field, reason] of [
      [1.5, undefined, "minimum-fraction-digits", "not-integer"],
      [-1, undefined, "minimum-fraction-digits", "negative"],
      [undefined, 1.5, "maximum-fraction-digits", "not-integer"],
      [undefined, -1, "maximum-fraction-digits", "negative"],
      [3, 2, "fraction-range", "minimum-exceeds-maximum"],
    ] as const) {
      reset(); const result = run(minimum, maximum, 42);
      equal(result.ok, false);
      if (result.ok) throw new Error("Expected fraction rejection");
      deepEqual(records, [validation(operation, field, reason)]);
      deepEqual(result.error.diagnosticRecord, records[0]);
    }
    for (const value of [NaN, Infinity, -Infinity]) {
      reset(); const result = run(undefined, undefined, value);
      equal(result.ok, false);
      if (result.ok) throw new Error("Expected nonfinite rejection");
      deepEqual(records, [validation(operation, valueField, "not-finite")]);
      deepEqual(result.error.params, { field: valueField, value: String(value) });
    }
    reset();
    const precedence = run(-1, -1, NaN);
    if (precedence.ok) throw new Error("Expected nonfinite result to win");
    deepEqual(records, [validation(operation, "minimum-fraction-digits", "negative"), validation(operation, valueField, "not-finite")]);
    deepEqual(precedence.error.params, { field: valueField, value: "NaN" });
    deepEqual(precedence.error.diagnosticRecord, records[1]);

    // Both arguments are projected before any fraction predicate, including throws.
    const order: string[] = [];
    const orderDiagnostics: CoreLocalizationDiagnosticOptions = { onDiagnostic(record) {
      records.push(record);
      const detail = record.detail as { field?: string };
      order.push("observed:" + detail.field);
    } };
    reset();
    const input = {
      get minimumFractionDigits() { order.push("minimum"); return -1; },
      get maximumFractionDigits() { order.push("maximum"); return undefined; },
      get value() { order.push("value"); return NaN; },
      get amount() { order.push("amount"); return NaN; },
      currency: currencyValue,
    };
    const result = operation === "number" ? localizableNumber(input as unknown as NumberInput, orderDiagnostics) : localizableCurrency(input as unknown as CurrencyInput, orderDiagnostics);
    equal(result.ok, false);
    deepEqual(order, ["minimum", "maximum", "observed:minimum-fraction-digits", valueField, "observed:" + valueField, valueField]);
    reset(); order.length = 0;
    const getterFailure = {
      get minimumFractionDigits() { order.push("minimum"); return -1; },
      get maximumFractionDigits(): never { order.push("maximum"); throw raw; },
      get value(): never { throw new Error("not reached"); },
      get amount(): never { throw new Error("not reached"); },
      currency: currencyValue,
    };
    throws(() => operation === "number" ? localizableNumber(getterFailure, selectedDiagnostics) : localizableCurrency(getterFailure, selectedDiagnostics), (cause) => cause === raw);
    deepEqual(order, ["minimum", "maximum"]);
    deepEqual(records, [boundary(operation, "input-projection", "maximum-fraction-digits"), ...source9]);

    // Actual integer rejection remains observed when String coercion later throws.
    reset();
    const conversionOrder: string[] = [];
    const hostileFraction = { toString(): never { conversionOrder.push("string"); throw raw; } };
    const formattingDiagnostics: CoreLocalizationDiagnosticOptions = { ...selectedDiagnostics, onDiagnostic(record, context) {
      records.push(record); contexts.push(context);
      conversionOrder.push(record.code === "core.localization.validation-rejected" ? "predicate" : "evidence");
    } };
    const formattingInput = { minimumFractionDigits: hostileFraction as never, maximumFractionDigits: undefined,
      get value(): never { throw new Error("finite check must not run"); },
      get amount(): never { throw new Error("finite check must not run"); }, currency: currencyValue };
    throws(() => operation === "number" ? localizableNumber(formattingInput as unknown as NumberInput, formattingDiagnostics) : localizableCurrency(formattingInput as unknown as CurrencyInput, formattingDiagnostics), (cause) => cause === raw);
    deepEqual(records, [validation(operation, "minimum-fraction-digits", "not-integer"), boundary(operation, "parameter-formatting", "minimum-fraction-digits"), ...source9]);
    deepEqual(conversionOrder.slice(0, 3), ["predicate", "string", "evidence"]);
    reset();
    let nonfiniteReads = 0;
    const hostileValue = { toString(): never { throw raw; } };
    const laterFormattingInput = {
      minimumFractionDigits: -1,
      get value() { nonfiniteReads++; return hostileValue as never; },
      get amount() { nonfiniteReads++; return hostileValue as never; },
      currency: currencyValue,
    };
    throws(() => operation === "number" ? localizableNumber(laterFormattingInput, selectedDiagnostics) : localizableCurrency(laterFormattingInput, selectedDiagnostics), (cause) => cause === raw);
    equal(nonfiniteReads, 2);
    deepEqual(records, [validation(operation, "minimum-fraction-digits", "negative"), validation(operation, valueField, "not-finite"), boundary(operation, "parameter-formatting", valueField), ...source9]);
  }
  // Repeated legacy reads remain repeated; no validation is invented on return projection.
  reset();
  let valueReads = 0, minimumReads = 0, maximumReads = 0;
  const changing = localizableNumber({
    get value() { return ++valueReads === 1 ? 42 : NaN; },
    get minimumFractionDigits() { minimumReads++; return minimumReads === 1 ? undefined : minimumReads; },
    get maximumFractionDigits() { maximumReads++; return maximumReads === 1 ? undefined : maximumReads; },
  } as NumberInput, diagnostics);
  if (!changing.ok) throw new Error("Expected legacy projection to remain accepted");
  equal(Number.isNaN(changing.value.value), true);
  equal(changing.value.minimumFractionDigits, 3); equal(changing.value.maximumFractionDigits, 3);
  equal(valueReads, 2); equal(minimumReads, 3); equal(maximumReads, 3); equal(records.length, 0);

  const request = { locale: localeValue, value: localizableDateTime({ value: dateValue }) };
  reset();
  const requestOrder: string[] = [];
  const text = { toString(): never { throw new Error("fixed helper must not format"); } };
  const fixed = fixedLocalizer(text as never, selectedDiagnostics);
  const fixedResult = fixed.format({
    get locale() { requestOrder.push("locale"); return localeValue; },
    get value() { requestOrder.push("value"); return {
      get kind() { requestOrder.push("kind"); return "date-time" as const; },
      get value(): never { throw new Error("fixed helper must not read date"); },
    }; },
  });
  if (!fixedResult.ok) throw new Error("Expected fixed formatting");
  equal(fixedResult.value.text, text); deepEqual(requestOrder, ["locale", "value", "kind"]); equal(records.length, 0);

  // Unsupported is a configured fact, even when later reason projection fails.
  let requestReads = 0, reasonReads = 0;
  const hostileRequest = new Proxy(request, { get(): never { requestReads++; throw raw; } });
  const reason = { get defaultMessage(): never { reasonReads++; throw raw; } };
  const unsupportedBound = unsupportedLocalizer(reason, selectedDiagnostics);
  equal(reasonReads, 0); equal(requestReads, 0);
  reset();
  throws(() => unsupportedBound.format(hostileRequest), (cause) => cause === raw);
  equal(reasonReads, 1); equal(requestReads, 0);
  deepEqual(records, [unsupported, boundary("format", "reason-projection", "default-message"), ...source9]);
  reset();
  const unsupportedResult = unsupportedLocalizer({}, selectedDiagnostics).format(hostileRequest);
  equal(requestReads, 0);
  if (unsupportedResult.ok) throw new Error("Expected unsupported");
  deepEqual(records, [unsupported]); deepEqual(unsupportedResult.error.diagnosticRecord, unsupported);
  let reasonMessageReads = 0;
  const dynamicReason = unsupportedLocalizer({
    defaultMessage: "",
    get messageKey() { return ++reasonMessageReads === 1 ? "fixture.key" : undefined; },
  } as NonNullable<Parameters<typeof unsupportedLocalizer>[0]>, selectedDiagnostics);
  reset();
  const dynamicResult = dynamicReason.format(hostileRequest);
  if (dynamicResult.ok) throw new Error("Expected unsupported");
  equal(dynamicResult.error.defaultMessage, ""); equal(dynamicResult.error.messageKey, undefined);
  equal(reasonMessageReads, 2); equal(requestReads, 0); deepEqual(records, [unsupported]);

  // Bound options are never merged/read when an explicit invocation override is supplied.
  let boundReads = 0;
  const hostileBound = Object.defineProperties({}, {
    diagnosticDefinitions: { get(): never { boundReads++; throw raw; } },
    onDiagnostic: { get(): never { boundReads++; throw raw; } },
  });
  const boundUnsupported = unsupportedLocalizer({}, hostileBound);
  equal(boundReads, 0);
  reset(); equal(boundUnsupported.format(hostileRequest, {}).ok, false); equal(boundReads, 0); equal(records.length, 0);
  equal(boundUnsupported.format(hostileRequest, selectedDiagnostics).ok, false); equal(boundReads, 0); deepEqual(records, [unsupported]);
  reset();
  const ordinaryBound = unsupportedLocalizer({}, selectedDiagnostics);
  equal(ordinaryBound.format(hostileRequest).ok, false);
  equal(ordinaryBound.format(hostileRequest, undefined).ok, false);
  deepEqual(records, [unsupported, unsupported]);
  reset();
  const throwingFixedRequest = { get locale(): never { throw raw; } } as never;
  throws(() => fixed.format(throwingFixedRequest, {}), (cause) => cause === raw); equal(records.length, 0);
  throws(() => fixed.format(throwingFixedRequest), (cause) => cause === raw);
  deepEqual(records, [boundary("format", "input-projection", "locale"), ...source9]);

  // Known guard errors rethrown by unrelated getters remain unknown current failures.
  const oldGuard = currencyCode("bad code");
  if (oldGuard.ok) throw new Error("Expected old guard");
  reset();
  throws(() => localizableDateTime({ get value(): never { throw oldGuard.error; } }, diagnostics), (cause) => cause === oldGuard.error);
  deepEqual(records, [boundary("date-time", "result-projection", "value"), oldGuard.error.diagnosticRecord]);
  for (const primitive of [undefined, null, 42, "LOCALIZATION-PRIVATE-CANARY", Object.freeze(new TypeError("LOCALIZATION-PRIVATE-CANARY"))]) {
    reset();
    throws(() => localizedFormat({ get locale(): never { throw primitive; } } as never, diagnostics), (cause) => cause === primitive);
    deepEqual(records, [boundary("localized-format", "result-projection", "locale")]);
  }
  reset();
  throws(() => currencyCode({ toString(): never { throw raw; } } as never, selectedDiagnostics), (cause) => cause === raw);
  deepEqual(records, [boundary("currency-code", "predicate-invocation", "currency"), ...source9]);
  reset();
  throws(() => regionCode({ toString() { return "GB"; }, toUpperCase(): never { throw raw; } } as never, selectedDiagnostics), (cause) => cause === raw);
  deepEqual(records, [boundary("region-code", "normalization", "region"), ...source9]);
  // Error factory keeps every legacy primary read and arbitrary primary identity.
  const oldPrimary = { private: "legacy-primary-pass-through" };
  const errorOrder: string[] = [];
  const errorInput = {
    get code() { errorOrder.push("code"); return "LOCALIZATION_INVALID_NUMBER" as const; },
    get defaultMessage() { errorOrder.push("default-message"); return "Legacy"; },
    get messageKey() { errorOrder.push("message-key"); return "fixture.key"; },
    get params() { errorOrder.push("params"); return {}; },
    get cause() { errorOrder.push("cause"); return raw; },
    get diagnostic() { errorOrder.push("diagnostic"); return diagnostic; },
    get diagnosticRecord() { errorOrder.push("diagnostic-record"); return oldPrimary as never; },
    get details() { errorOrder.push("details"); return {}; },
  };
  reset();
  equal(localizationError(errorInput, selectedDiagnostics).diagnosticRecord, oldPrimary);
  deepEqual(errorOrder, ["code", "default-message", "message-key", "message-key", "params", "params", "cause", "cause", "diagnostic", "diagnostic", "diagnostic-record", "diagnostic-record", "details", "details"]);
  equal(records.length, 0);
  reset();
  throws(() => localizationError({ code: "LOCALIZATION_INVALID_NUMBER", defaultMessage: "Legacy", get cause(): never { throw raw; } }, selectedDiagnostics), (cause) => cause === raw);
  deepEqual(records, [boundary("error", "error-projection", "cause"), ...source9]);

  // Data-only source selection; no arbitrary accessors/provider objects reach the sink.
  reset();
  throws(() => fixedLocalizer("", diagnostics).format(throwingFixedRequest), (cause) => cause === raw);
  deepEqual(records, [boundary("format", "input-projection", "locale")]);
  let evidenceReads = 0;
  const accessorSource = Object.defineProperty({}, "diagnosticRecord", { get() { evidenceReads++; return source9[0]; } });
  reset();
  throws(() => localizedFormat({ get locale(): never { throw accessorSource; } } as never, selectedDiagnostics), (cause) => cause === accessorSource);
  equal(evidenceReads, 0); equal(records.length, 1);
  for (const malformed of [
    { diagnosticRecord: { ...source9[0], detail: { private: "LOCALIZATION-PRIVATE-CANARY" } } },
    new Proxy({}, { getOwnPropertyDescriptor(): never { throw raw; } }),
  ]) {
    reset();
    throws(() => localizedFormat({ get locale(): never { throw malformed; } } as never, selectedDiagnostics), (cause) => cause === malformed);
    equal(records.length, 1);
  }
  reset();
  throws(() => localizedFormat({ get locale(): never { throw raw; } } as never, selectedDiagnostics), (cause) => cause === raw);
  equal(records.length, 10);
  equal(contexts.every((context) => context.operation === "localized-format" && context.phase === "result-projection" && context.field === "locale"), true);
  equal(JSON.stringify(records).includes("LOCALIZATION-PRIVATE-CANARY"), false);
  for (const definition of coreLocalizationDiagnosticDefinitions) {
    equal(parseDiagnosticRecord<unknown>(definition, { schema: "core/diagnostic-record/v1", code: definition.code, definitionVersion: 1, detail: { private: "LOCALIZATION-PRIVATE-CANARY" } }).ok, false);
  }
  deepEqual(coreLocalizationDiagnosticDefinitions[1]!.classification, {
    failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", retryable: false, userCorrectable: false, action: "none",
  });
  reset();
  observeCoreLocalizationDiagnostic(diagnostics, { ...coreLocalizationBoundaryDiagnosticRecord({ operation: "number", phase: "predicate-invocation", reason: "threw", effect: "value-not-produced" }), detail: { private: "LOCALIZATION-PRIVATE-CANARY" } }, raw);
  equal(records.length, 0);

  // Native calls retain their original non-callable TypeError text.
  const nativeMessage = (action: () => unknown) => {
    try { action(); } catch (cause) {
      equal(cause instanceof TypeError, true); return (cause as TypeError).message;
    }
    throw new Error("Expected native error");
  };
  const normalizedValue = { toString() { return "USD"; }, toUpperCase: 17 };
  const oldUpper = (value: string) => value.toUpperCase();
  const upperMessage = nativeMessage(() => oldUpper(normalizedValue as never));
  throws(() => currencyCode(normalizedValue as never), (cause) => cause instanceof TypeError && cause.message === upperMessage);
  const includesValue = { toString() { return "Europe/London"; }, includes: 17 };
  const oldIncludes = (value: string) => value.includes("..");
  const includesMessage = nativeMessage(() => oldIncludes(includesValue as never));
  throws(() => timeZoneId(includesValue as never), (cause) => cause instanceof TypeError && cause.message === includesMessage);
  for (const method of ["isFinite", "isInteger"] as const) {
    const descriptor = Object.getOwnPropertyDescriptor(Number, method)!;
    Object.defineProperty(Number, method, { ...descriptor, value: 17 });
    try {
      const message = nativeMessage(() => method === "isFinite" ? Number.isFinite(42) : Number.isInteger(1));
      throws(() => localizableNumber(method === "isFinite" ? { value: 42 } : { value: 42, minimumFractionDigits: 1 }), (cause) => cause instanceof TypeError && cause.message === message);
    } finally { Object.defineProperty(Number, method, descriptor); }
  }

  // Observer failures never await/replay/replace the original result.
  let shadowReads = 0, thenableCalls = 0;
  const nativeRejected = Promise.reject(raw);
  Object.defineProperty(nativeRejected, "then", { get(): never { shadowReads++; throw raw; } });
  for (const options of [
    { onDiagnostic(): never { throw raw; } },
    { onDiagnostic() { return nativeRejected; } },
    { onDiagnostic() { return { then(_resolve: unknown, reject: (cause: unknown) => void) { thenableCalls++; reject(raw); } }; } },
    Object.defineProperty({}, "onDiagnostic", { get(): never { throw raw; } }),
  ]) {
    equal(currencyCode("bad code", options).ok, false);
  }
  reset();
  throws(() => localizedFormat({ get locale(): never { throw raw; } } as never, Object.defineProperty({ onDiagnostic: selectedDiagnostics.onDiagnostic! }, "diagnosticDefinitions", { get(): never { throw raw; } })), (cause) => cause === raw);
  equal(records.length, 1); equal(JSON.stringify(records).includes("LOCALIZATION-PRIVATE-CANARY"), false);
  await new Promise((resolve) => setTimeout(resolve, 0));
  equal(shadowReads, 0); equal(thenableCalls, 1);
}
void localizationDiagnosticProof().then(() => console.log("packages/core localization runtime test passed."));
