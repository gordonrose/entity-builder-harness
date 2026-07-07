import { deepEqual, equal, throws } from "node:assert/strict";
import {
  eventEnvelope,
  eventId,
  eventPublishError,
  eventType,
  eventVersion,
  inMemoryEventBus,
  noopEventBus,
  type EventEnvelope,
  type EventHandler,
} from "../src/events/index";
import { correlationId, isErr, isOk, isoDateTime } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

async function main(): Promise<void> {
  const validType = eventType("deal.updated");
  equal(isOk(validType), true);
  if (!isOk(validType)) {
    throw new Error("Expected event type to be valid.");
  }
  equal(validType.value, "deal.updated");

  const invalidType = eventType("Deal Updated");
  equal(isErr(invalidType), true);
  if (!isErr(invalidType)) {
    throw new Error("Expected event type to be invalid.");
  }
  equal(invalidType.error.code, "EVENT_INVALID_TYPE");
  equal(invalidType.error.messageKey, "events.type.invalid");

  const validVersion = eventVersion(1);
  equal(isOk(validVersion), true);
  if (!isOk(validVersion)) {
    throw new Error("Expected event version to be valid.");
  }
  equal(validVersion.value, 1);

  const invalidVersion = eventVersion(0);
  equal(isErr(invalidVersion), true);
  if (!isErr(invalidVersion)) {
    throw new Error("Expected event version to be invalid.");
  }
  equal(invalidVersion.error.code, "EVENT_INVALID_VERSION");
  equal(invalidVersion.error.messageKey, "events.version.invalid");

  const occurredAt = isoDateTime("2026-07-07T12:00:00.000Z");
  equal(isOk(occurredAt), true);
  if (!isOk(occurredAt)) {
    throw new Error("Expected timestamp to be valid.");
  }

  const payload = {
    dealId: "deal-123",
    participants: ["principal-123"],
    metadata: { stage: "qualified", score: 12 },
  };
  const event = eventEnvelope({
    id: eventId("event-123"),
    type: validType.value,
    version: validVersion.value,
    occurredAt: occurredAt.value,
    tenantId: tenantId("tenant-123"),
    correlationId: correlationId("request-123"),
    payload,
  });

  deepEqual(event, {
    id: "event-123",
    type: "deal.updated",
    version: 1,
    occurredAt: "2026-07-07T12:00:00.000Z",
    tenantId: "tenant-123",
    correlationId: "request-123",
    payload: {
      dealId: "deal-123",
      participants: ["principal-123"],
      metadata: { stage: "qualified", score: 12 },
    },
  });

  payload.participants.push("principal-456");
  payload.metadata.stage = "mutated";
  deepEqual(event.payload, {
    dealId: "deal-123",
    participants: ["principal-123"],
    metadata: { stage: "qualified", score: 12 },
  });

  const explicitError = eventPublishError({
    code: "EVENT_PUBLISH_FAILED",
    defaultMessage: "Event publish failed.",
    messageKey: "events.publish.failed",
  });
  equal(explicitError.code, "EVENT_PUBLISH_FAILED");
  equal(explicitError.messageKey, "events.publish.failed");

  const handledTypes: string[] = [];
  const handler: EventHandler = {
    handle: (publishedEvent) => {
      handledTypes.push(publishedEvent.type);
    },
  };
  const bus = inMemoryEventBus({ handlers: [handler] });
  const publishResult = await bus.publish([event]);
  equal(isOk(publishResult), true);
  deepEqual(handledTypes, ["deal.updated"]);
  deepEqual(bus.publishedEvents(), [event]);

  const storedEvents = bus.publishedEvents() as EventEnvelope<typeof event.payload>[];
  const storedPayload = storedEvents[0]?.payload;
  if (storedPayload === undefined) {
    throw new Error("Expected stored event payload.");
  }
  storedPayload.participants.push("principal-789");
  deepEqual(bus.publishedEvents()[0]?.payload, {
    dealId: "deal-123",
    participants: ["principal-123"],
    metadata: { stage: "qualified", score: 12 },
  });

  const failingBus = inMemoryEventBus({
    handlers: [
      {
        handle: () => {
          throw new Error("handler failed");
        },
      },
    ],
  });
  const failedPublish = await failingBus.publish([event]);
  equal(isErr(failedPublish), true);
  if (!isErr(failedPublish)) {
    throw new Error("Expected publish failure.");
  }
  equal(failedPublish.error.code, "EVENT_HANDLER_FAILED");
  equal(failedPublish.error.messageKey, "events.handler.failed");
  deepEqual(failingBus.publishedEvents(), []);

  const invalidPayloadEvent = () =>
    eventEnvelope({
      id: eventId("event-invalid-payload"),
      type: validType.value,
      version: validVersion.value,
      occurredAt: occurredAt.value,
      payload: { score: Number.POSITIVE_INFINITY },
    });
  throws(invalidPayloadEvent, /finite numbers/);

  const noopResult = await noopEventBus.publish([event]);
  equal(isOk(noopResult), true);
}

main()
  .then(() => {
    console.log("packages/core events runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
