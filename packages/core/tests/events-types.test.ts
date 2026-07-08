import {
  eventEnvelope,
  eventId,
  eventPublishError,
  eventType,
  eventVersion,
  inMemoryEventBus,
  noopEventBus,
  type EventBus,
  type EventEnvelope,
  type EventHandler,
  type EventPayload,
  type EventPayloadValue,
  type EventPublishError,
  type EventPublishErrorCode,
  type EventPublisher,
  type EventType,
  type EventVersion,
} from "../src/events/index";
import { causationId, correlationId, isOk, isoDateTime, type Result } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

const typeResult: Result<EventType, EventPublishError> = eventType("deal.updated");
const versionResult: Result<EventVersion, EventPublishError> = eventVersion(1);
const acceptedCode: EventPublishErrorCode = "EVENT_HANDLER_FAILED";
const acceptedError: EventPublishError = eventPublishError({
  code: acceptedCode,
  defaultMessage: "An event handler failed.",
  messageKey: "events.handler.failed",
});
const payloadValue: EventPayloadValue = {
  dealId: "deal-123",
  participants: ["principal-123"],
  metadata: { stage: "qualified", score: 12, archived: false },
};
const payload: EventPayload = {
  dealId: "deal-123",
  stage: "qualified",
  score: 12,
};
const timestamp = isoDateTime("2026-07-07T12:00:00.000Z");

if (!isOk(typeResult) || !isOk(versionResult) || !isOk(timestamp)) {
  throw new Error("Expected valid test primitives.");
}

const event: EventEnvelope<EventPayload> = eventEnvelope({
  id: eventId("event-123"),
  type: typeResult.value,
  version: versionResult.value,
  occurredAt: timestamp.value,
  tenantId: tenantId("tenant-123"),
  correlationId: correlationId("request-123"),
  causationId: causationId("queue-message-123"),
  payload,
});
const handler: EventHandler = {
  handle: (_event) => undefined,
};
const bus: EventBus = inMemoryEventBus({ handlers: [handler] });
const publisher: EventPublisher = noopEventBus;

void acceptedError;
void payloadValue;
void event;
void bus;
void publisher;

bus.publish([event]);
publisher.publish([event]);

// @ts-expect-error event types must be explicitly created and branded.
const invalidType: EventType = "deal.updated";
void invalidType;

// @ts-expect-error event versions must be explicitly created and branded.
const invalidVersion: EventVersion = 1;
void invalidVersion;

// @ts-expect-error event payloads must stay plain and serializable.
const invalidPayload: EventPayloadValue = new Date();
void invalidPayload;

eventEnvelope({
  // @ts-expect-error event envelopes require a branded event id.
  id: "event-123",
  type: typeResult.value,
  version: versionResult.value,
  occurredAt: timestamp.value,
  payload,
});

eventEnvelope({
  id: eventId("event-123"),
  // @ts-expect-error event envelopes require a branded event type.
  type: "deal.updated",
  version: versionResult.value,
  occurredAt: timestamp.value,
  payload,
});

eventEnvelope({
  id: eventId("event-123"),
  type: typeResult.value,
  // @ts-expect-error event envelopes require a branded positive event version.
  version: 1,
  occurredAt: timestamp.value,
  payload,
});

// @ts-expect-error event publish error codes are constrained.
eventPublishError({ code: "EVENT_BROKER_LOCKED", defaultMessage: "Broker locked." });
