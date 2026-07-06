import { equal, notEqual } from "node:assert/strict";
import {
  correlationId,
  err,
  fixedClock,
  isErr,
  isOk,
  isoDateTime,
  isoDateTimeFromDate,
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

const invalid = isoDateTime("not a date");
equal(invalid.ok, false);
equal(isErr(invalid), true);
if (!isErr(invalid)) {
  throw new Error("Expected ISO date-time parsing to fail.");
}
equal(invalid.error.code, "INVALID_ISO_DATE_TIME");

const success = ok({ enabled: true });
equal(isOk(success), true);
if (!isOk(success)) {
  throw new Error("Expected result to be ok.");
}
equal(success.value.enabled, true);

const failure = err({ code: "TEST_FAILURE", message: "Expected failure." });
equal(isErr(failure), true);
if (!isErr(failure)) {
  throw new Error("Expected result to be err.");
}
equal(failure.error.code, "TEST_FAILURE");

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
