import { correlationId, entityId, fixedClock, isoDateTimeFromDate, requestContext, type Clock, type ISODateTime } from "../../../../src/shared/index";

const requestId = correlationId("request-789");
const tenantId = entityId<"TenantId">("tenant-123");

const timestamp: ISODateTime = isoDateTimeFromDate(new Date("2026-07-06T12:00:00Z"));
const acceptedClock: Clock = fixedClock(new Date("2026-07-06T12:00:00Z"));
const acceptedClockReading: Date = acceptedClock.now();
void acceptedClockReading;

// @ts-expect-error canonical timestamps must be branded, not arbitrary strings.
const rejectedTimestamp: ISODateTime = "2026-07-06T12:00:00.000Z";
void rejectedTimestamp;

// @ts-expect-error a timestamp does not permit null.
const rejectedNullTimestamp: ISODateTime = null;
void rejectedNullTimestamp;

// @ts-expect-error clocks return Date values, not branded timestamp strings.
const rejectedClock: Clock = { now: () => timestamp };
void rejectedClock;

// @ts-expect-error fixed clocks require a Date, not a timestamp string.
fixedClock(timestamp);

const context = requestContext({ correlationId: requestId, now: timestamp });
const acceptedDateContext = requestContext({ correlationId: requestId, now: acceptedClockReading });
void acceptedDateContext;

// @ts-expect-error string timestamps must be validated/branded before creating context.
requestContext({ correlationId: requestId, now: "2026-07-06T12:00:00.000Z" });

// @ts-expect-error request context must receive a CorrelationId, not an arbitrary entity ID.
requestContext({ correlationId: tenantId, now: timestamp });

void context;
