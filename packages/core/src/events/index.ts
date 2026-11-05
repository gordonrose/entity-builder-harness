import {
  brand,
  copyJsonValue,
  entityId,
  err,
  messageKey,
  ok,
  type Brand,
  type CausationId,
  type CoreError,
  type CorrelationId,
  type EntityId,
  type ISODateTime,
  type JsonValue,
  type MessageKey,
  type MessageParams,
  type Result,
} from "../shared/index";
import { parseRelatedDiagnosticRecords, type DiagnosticDescriptor, type DiagnosticRecord } from "../diagnostics/index";
import type { TenantId } from "../tenancy/index";
import { EventObservation } from "./observations";
import type { CoreEventDiagnosticOptions, CoreEventErrorEvidence } from "./diagnostics";
export { coreEventDiagnosticDefinitions, coreEventValidationDiagnostic, coreEventBoundaryDiagnostic } from "./diagnostics";
export type { CoreEventDiagnosticOptions, CoreEventDiagnosticContext, CoreEventErrorEvidence, CoreEventValidationDetail, CoreEventBoundaryDetail } from "./diagnostics";

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
  readonly causationId?: CausationId;
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

export function eventType(value: string, diagnostics?: CoreEventDiagnosticOptions): Result<EventType, EventPublishError> {
  const observation = new EventObservation("event-type", diagnostics);
  return observation.run(() => {
  if (!observation.at("predicate", "type", () => eventTypePattern.test(value))) {
    const diagnosticRecord = observation.validation({ operation: "event-type", field: "type", reason: "invalid-format" });
    return err(
      eventPublishError({
        code: "EVENT_INVALID_TYPE",
        defaultMessage: "Event type must use dot-separated lowercase segments.",
        messageKey: "events.type.invalid",
        params: { type: value },
        ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
      }),
    );
  }

  return ok(brand<string, "EventType">(value));
  });
}

export function eventVersion(value: number, diagnostics?: CoreEventDiagnosticOptions): Result<EventVersion, EventPublishError> {
  const observation = new EventObservation("event-version", diagnostics);
  return observation.run(() => {
  let reason: "not-integer" | "not-positive" = "not-integer";
  if (observation.at("predicate", "version", () => (!Number.isInteger(value) && (reason = "not-integer", true)) || (value <= 0 && (reason = "not-positive", true)))) {
    const diagnosticRecord = observation.validation({ operation: "event-version", field: "version", reason });
    return err(
      eventPublishError({
        code: "EVENT_INVALID_VERSION",
        defaultMessage: "Event version must be a positive integer.",
        messageKey: "events.version.invalid",
        params: { version: observation.at("parameter-formatting", "version", () => String(value)) },
        ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
      }),
    );
  }

  return ok(brand<number, "EventVersion">(value));
  });
}

export function eventPublishError(input: {
  readonly code: EventPublishErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly diagnostic?: DiagnosticDescriptor;
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly details?: Readonly<Record<string, unknown>>;
}, evidence?: CoreEventErrorEvidence): EventPublishError {
  const related = eventRelatedEvidence(evidence);
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.diagnostic === undefined ? {} : { diagnostic: input.diagnostic }),
    ...(input.diagnosticRecord === undefined ? {} : { diagnosticRecord: input.diagnosticRecord }),
    ...(related === undefined ? {} : { relatedDiagnosticRecords: related }),
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
  readonly causationId?: CausationId;
  readonly payload: TPayload;
}, diagnostics?: CoreEventDiagnosticOptions): EventEnvelope<TPayload> {
  const observation = new EventObservation("envelope", diagnostics);
  return observation.run(() => projectEventEnvelope(input, observation, "input-projection"));
}

function projectEventEnvelope<TPayload extends EventPayloadValue>(input: EventEnvelope<TPayload>, observation: EventObservation,
  phase: "input-projection" | "batch-copy" | "handler-argument-copy" | "snapshot-copy"): EventEnvelope<TPayload> {
  return {
    id: observation.at(phase, "id", () => input.id),
    type: observation.at(phase, "type", () => input.type),
    version: observation.at(phase, "version", () => input.version),
    occurredAt: observation.at(phase, "occurred-at", () => input.occurredAt),
    ...observation.at(phase, "tenant-id", () => input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...observation.at(phase, "correlation-id", () => input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...observation.at(phase, "causation-id", () => input.causationId === undefined ? {} : { causationId: input.causationId }),
    payload: observation.at(phase, "payload", () => { const value = input.payload; return observation.at("payload-copy", "payload", () => copyEventPayloadValue(value)); }) as TPayload,
  };
}

export function inMemoryEventBus(options: {
  readonly handlers?: readonly EventHandler[];
} = {}, diagnostics?: CoreEventDiagnosticOptions): InMemoryEventBus {
  const declaration = new EventObservation("bus-construction", diagnostics);
  declaration.effectIs("bus-not-created");
  const published: EventEnvelope[] = [];
  const handlers = declaration.run(() => declaration.at("handler-declaration", "handlers", () => [...(options.handlers ?? [])]));

  return {
    async publish(events) {
      const observation = new EventObservation("publish", diagnostics);
      observation.effectIs("publish-not-appended");
      try {
      const copiedEvents = observation.at("batch-copy", "events", () => events.map((event) => projectEventEnvelope(event, observation, "batch-copy")));

      let eventOrdinal = 0;
      observation.location("event-iteration", "events");
      for (const event of copiedEvents) {
        observation.eventAt(eventOrdinal++);
        let handlerOrdinal = 0;
        observation.location("handler-iteration", "handlers");
        for (const handler of handlers) {
          observation.handlerAt(handlerOrdinal++);
          let completing = false;
          observation.handlerIs("not-invoked");
          try {
            observation.location("handler-selection", "handler");
            let argument: EventEnvelope;
            const pending = handler.handle((argument = observation.at("handler-argument-copy", undefined, () => projectEventEnvelope(event, observation, "handler-argument-copy")),
              observation.location("handler-invocation", "handler"), observation.handlerIs("unknown"), argument));
            observation.location("handler-completion", "handler"); completing = true;
            await pending;
          } catch (cause) {
            const evidence = observation.failed(cause, completing ? "rejected" : "threw");
            return err(
              eventPublishError({
                code: "EVENT_HANDLER_FAILED",
                defaultMessage: "An event handler failed while processing a published event.",
                messageKey: "events.handler.failed",
                cause,
                ...(evidence.diagnosticRecord === undefined ? {} : { diagnosticRecord: evidence.diagnosticRecord }),
                details: {
                  eventId: observation.at("input-projection", "id", () => event.id),
                  eventType: observation.at("input-projection", "type", () => event.type),
                  eventVersion: observation.at("input-projection", "version", () => event.version),
                },
              }, { ...(evidence.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: evidence.relatedDiagnosticRecords }), relatedDiagnosticDefinitions: evidence.definitions }),
            );
          }
          observation.handlerIs(undefined);
          observation.handlerAt(undefined);
          observation.location("handler-iteration", "handlers");
        }
        observation.eventAt(undefined);
        observation.location("event-iteration", "events");
      }

      observation.location("published-append", "events"); observation.effectIs("append-outcome-unknown");
      published.push(...copiedEvents);
      return ok(undefined);
      } catch (cause) { observation.failed(cause); throw cause; }
    },

    publishedEvents() {
      const observation = new EventObservation("published-events", diagnostics);
      observation.effectIs("snapshot-not-returned");
      return observation.run(() => observation.at("snapshot-copy", "events", () => published.map((event) => projectEventEnvelope(event, observation, "snapshot-copy"))));
    },
  };
}

export const noopEventBus: EventBus = {
  publish: async () => ok(undefined),
};

const eventTypePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/;

function copyEventPayloadValue(value: EventPayloadValue): EventPayloadValue {
  return copyJsonValue(value, "event payload");
}

function eventRelatedEvidence(evidence: CoreEventErrorEvidence | undefined): readonly DiagnosticRecord[] | undefined {
  if (evidence === undefined) return undefined;
  try {
    const records = Object.getOwnPropertyDescriptor(evidence, "relatedDiagnosticRecords");
    if (records === undefined || !("value" in records) || records.value === undefined) return undefined;
    const definitions = Object.getOwnPropertyDescriptor(evidence, "relatedDiagnosticDefinitions");
    if (definitions !== undefined && !("value" in definitions)) return undefined;
    const checked = parseRelatedDiagnosticRecords(definitions?.value ?? [], records.value);
    return checked.ok ? checked.value : undefined;
  } catch { return undefined; }
}
