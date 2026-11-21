import { deepEqual, equal } from "node:assert/strict";
import { isErr, isOk, isoDateTime, isoDateTimeFromDate } from "../../../../src/shared/index";

for (const [label, input, expected] of [
  ["UTC gains milliseconds", "2026-07-06T14:30:00Z", "2026-07-06T14:30:00.000Z"],
  ["positive offset becomes UTC", "2026-07-06T14:30:00+02:00", "2026-07-06T12:30:00.000Z"],
  ["negative offset crosses the UTC day boundary", "2026-07-06T23:30:00-02:00", "2026-07-07T01:30:00.000Z"],
  ["fractional seconds retain milliseconds", "2026-07-06T14:30:00.123Z", "2026-07-06T14:30:00.123Z"],
] as const) {
  const actual = isoDateTime(input);

  equal(isOk(actual), true, label);
  deepEqual(actual, { ok: true, value: expected }, label);
}

for (const [label, input, reason] of [
  ["empty text is not a date-time", "", "invalid-format"],
  ["malformed private input is not copied into its diagnostic", "synthetic-private-date", "invalid-format"],
  ["date-only input is rejected", "2026-07-06", "invalid-format"],
  ["prose date input is rejected", "July 6, 2026", "invalid-format"],
  ["timezone is required", "2026-07-06T14:30:00", "invalid-format"],
  ["formatted but unparseable month is distinguished", "2026-99-06T14:30:00Z", "parse-rejected"],
] as const) {
  const actual = isoDateTime(input);

  equal(isErr(actual), true, label);
  if (!isErr(actual)) throw new Error(`${label}: expected a date-time failure.`);
  equal(actual.error.code, "INVALID_ISO_DATE_TIME", label);
  equal(actual.error.defaultMessage, "Expected a valid ISO date-time string.", label);
  deepEqual(actual.error.details, { value: input }, `${label}: preserve the existing error contract`);
  deepEqual(actual.error.diagnosticRecord, {
    schema: "core/diagnostic-record/v1",
    code: "core.shared.date-invalid",
    definitionVersion: 1,
    detail: { reason },
  }, `${label}: exact reason and no raw input in diagnostic detail`);
}

equal(
  isoDateTimeFromDate(new Date("2026-07-06T14:30:00+02:00")),
  "2026-07-06T12:30:00.000Z",
  "Date conversion produces the same canonical UTC representation",
);

console.log("packages/core shared time date-time unit tests passed.");
