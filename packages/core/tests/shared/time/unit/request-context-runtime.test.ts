import { deepEqual, equal } from "node:assert/strict";
import { correlationId, isoDateTimeFromDate, requestContext } from "../../../../src/shared/index";

const fixedNow = new Date("2026-07-06T12:00:00Z");
const context = requestContext({
  correlationId: correlationId("request-123"),
  now: fixedNow,
});
equal(context.correlationId, "request-123");
equal(context.now, "2026-07-06T12:00:00.000Z", "request context normalizes its Date input");

const brandedNow = isoDateTimeFromDate(new Date("2026-07-06T12:00:00Z"));
deepEqual(requestContext({ correlationId: correlationId("request-456"), now: brandedNow }), {
  correlationId: "request-456",
  now: "2026-07-06T12:00:00.000Z",
}, "request context preserves an already-branded timestamp");

console.log("packages/core shared time request-context unit tests passed.");
