import {
  brand,
  copyJsonValue,
  entityId,
  err,
  messageKey,
  ok,
  type Brand,
  type CoreError,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type JsonValue,
  type MessageKey,
  type MessageParams,
  type Result,
} from "../shared/index";
import type { TenantId } from "../tenancy/index";

export type EventId = EntityId<"EventId">;
export type EventType = Brand<string, "EventType">;
export type EventVersion = Brand<number, "EventVersion">;
export type EventPayloadValue = JsonValue;
export type EventPayload = Readonly<Record<string, EventPayloadValue>>;

export type EventPublishErrorCode =
  | "EVENT_HANDLER_FAILED"
  | "EVENT_INVALID_TYPE"
  | "EVENT_INVALID_VERSION"
  | "EVENT_PUBLISH_FAILED";

export interface EventPublishError extends CoreError {
  readonly code: EventPublishErrorCode;
}

export interface EventEnvelope<TPayload extends EventPayloadValue = EventPayload> {
  readonly id: EventId;
  readonly type: EventType;
  readonly version: EventVersion;
  readonly occurredAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly payload: TPayload;
}

export interface EventHandler<TEvent extends EventEnvelope = EventEnvelope> {
  handle(event: TEvent): Promise<void> | void;
}

export interface EventPublisher {
  publish(events: readonly EventEnvelope[]): Promise<Result<void, EventPublishError>>;
}

export type EventBus = EventPublisher;

export interface InMemoryEventBus extends EventBus {
  publishedEvents(): readonly EventEnvelope[];
}

export function eventId(value: string): EventId {
  return entityId<"EventId">(value);
}

export function eventType(value: string): Result<EventType, EventPublishError> {
  if (!eventTypePattern.test(value)) {
    return err(
      eventPublishError({
        code: "EVENT_INVALID_TYPE",
        defaultMessage: "Event type must use dot-separated lowercase segments.",
        messageKey: "events.type.invalid",
        params: { type: value },
      }),
    );
  }

  return ok(brand<string, "EventType">(value));
}

export function eventVersion(value: number): Result<EventVersion, EventPublishError> {
  if (!Number.isInteger(value) || value <= 0) {
    return err(
      eventPublishError({
        code: "EVENT_INVALID_VERSION",
        defaultMessage: "Event version must be a positive integer.",
        messageKey: "events.version.invalid",
        params: { version: String(value) },
      }),
    );
  }

  return ok(brand<number, "EventVersion">(value));
}

export function eventPublishError(input: {
  readonly code: EventPublishErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly details?: Readonly<Record<string, unknown>>;
}): EventPublishError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}

export function eventEnvelope<TPayload extends EventPayloadValue>(input: {
  readonly id: EventId;
  readonly type: EventType;
  readonly version: EventVersion;
  readonly occurredAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly payload: TPayload;
}): EventEnvelope<TPayload> {
  return {
    id: input.id,
    type: input.type,
    version: input.version,
    occurredAt: input.occurredAt,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    payload: copyEventPayloadValue(input.payload) as TPayload,
  };
}

export function inMemoryEventBus(options: {
  readonly handlers?: readonly EventHandler[];
} = {}): InMemoryEventBus {
  const published: EventEnvelope[] = [];
  const handlers = [...(options.handlers ?? [])];

  return {
    async publish(events) {
      const copiedEvents = events.map(copyEventEnvelope);

      for (const event of copiedEvents) {
        for (const handler of handlers) {
          try {
            await handler.handle(copyEventEnvelope(event));
          } catch (cause) {
            return err(
              eventPublishError({
                code: "EVENT_HANDLER_FAILED",
                defaultMessage: "An event handler failed while processing a published event.",
                messageKey: "events.handler.failed",
                cause,
                details: {
                  eventId: event.id,
                  eventType: event.type,
                  eventVersion: event.version,
                },
              }),
            );
          }
        }
      }

      published.push(...copiedEvents);
      return ok(undefined);
    },

    publishedEvents() {
      return published.map(copyEventEnvelope);
    },
  };
}

export const noopEventBus: EventBus = {
  publish: async () => ok(undefined),
};

const eventTypePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/;

function copyEventEnvelope<TPayload extends EventPayloadValue>(event: EventEnvelope<TPayload>): EventEnvelope<TPayload> {
  return eventEnvelope(event);
}

function copyEventPayloadValue(value: EventPayloadValue): EventPayloadValue {
  return copyJsonValue(value, "event payload");
}
