import { equal, notEqual } from "node:assert/strict";
import {
  correlationId,
  err,
  fixedClock,
  isErr,
  isOk,
  isoDateTime,
  isoDateTimeFromDate,
  messageDescriptor,
  messageKey,
  ok,
  requestContext,
} from "../src/shared/index";

const parsed = isoDateTime("2026-07-06T14:30:00Z");
equal(parsed.ok, true);
equal(isOk(parsed), true);
if (!isOk(parsed)) {
  throw new Error("Expected ISO date-time parsing to succeed.");
}
equal(parsed.value, "2026-07-06T14:30:00.000Z");

const parsedOffset = isoDateTime("2026-07-06T14:30:00+02:00");
equal(parsedOffset.ok, true);
if (!isOk(parsedOffset)) {
  throw new Error("Expected ISO date-time with offset parsing to succeed.");
}
equal(parsedOffset.value, "2026-07-06T12:30:00.000Z");

const invalid = isoDateTime("not a date");
equal(invalid.ok, false);
equal(isErr(invalid), true);
if (!isErr(invalid)) {
  throw new Error("Expected ISO date-time parsing to fail.");
}
equal(invalid.error.code, "INVALID_ISO_DATE_TIME");
equal(invalid.error.defaultMessage, "Expected a valid ISO date-time string.");

const dateOnly = isoDateTime("2026-07-06");
equal(dateOnly.ok, false);

const proseDate = isoDateTime("July 6, 2026");
equal(proseDate.ok, false);

const noTimezone = isoDateTime("2026-07-06T14:30:00");
equal(noTimezone.ok, false);

const descriptor = messageDescriptor({
  code: "VALIDATION_REQUIRED",
  defaultMessage: "Field is required.",
  messageKey: "validation.required",
  params: { field: "email" },
});
equal(descriptor.messageKey, messageKey("validation.required"));
equal(descriptor.params?.field, "email");

const success = ok({ enabled: true });
equal(isOk(success), true);
if (!isOk(success)) {
  throw new Error("Expected result to be ok.");
}
equal(success.value.enabled, true);

const failure = err({ code: "TEST_FAILURE", defaultMessage: "Expected failure." });
equal(isErr(failure), true);
if (!isErr(failure)) {
  throw new Error("Expected result to be err.");
}
equal(failure.error.code, "TEST_FAILURE");
equal(failure.error.defaultMessage, "Expected failure.");

const fixedNow = new Date("2026-07-06T12:00:00Z");
const clock = fixedClock(fixedNow);
equal(clock.now().toISOString(), "2026-07-06T12:00:00.000Z");
notEqual(clock.now(), fixedNow);

const context = requestContext({
  correlationId: correlationId("request-123"),
  now: fixedNow,
});
equal(context.correlationId, "request-123");
equal(context.now, isoDateTimeFromDate(fixedNow));

console.log("packages/core shared runtime test passed.");
