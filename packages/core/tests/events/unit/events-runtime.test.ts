import { deepEqual, equal, throws, rejects } from "node:assert/strict";
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
  type CoreEventDiagnosticOptions,
} from "../../../src/events/index";
import { diagnosticDescriptor, defineDiagnostic, createDiagnosticRecord, type DiagnosticRecord } from "../../../src/diagnostics/index";
import { causationId, correlationId, isErr, isOk, isoDateTime } from "../../../src/shared/index";
import { tenantId } from "../../../src/tenancy/index";

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
    causationId: causationId("queue-message-123"),
    payload,
  });

  deepEqual(event, {
    id: "event-123",
    type: "deal.updated",
    version: 1,
    occurredAt: "2026-07-07T12:00:00.000Z",
    tenantId: "tenant-123",
    correlationId: "request-123",
    causationId: "queue-message-123",
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
    diagnostic: diagnosticDescriptor({
      failureKind: "dependency_unavailable",
      failureSource: "platform",
      severity: "error",
      recovery: "automation_retryable",
      action: "retry",
    }),
  });
  equal(explicitError.code, "EVENT_PUBLISH_FAILED");
  equal(explicitError.messageKey, "events.publish.failed");
  equal(explicitError.diagnostic?.retryable, true);

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
  await diagnosticCoverage(event);
}

async function diagnosticCoverage(event: EventEnvelope): Promise<void> {
  const sourceDefinition = defineDiagnostic({ code: "fixture.events-source", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } } } as const);
  const sourceRecords = Array.from({ length: 9 }, (_, ordinal) => { const result = createDiagnosticRecord(sourceDefinition, { ordinal }); if (!result.ok) throw result.error; return result.value; });
  const fresh = () => Object.freeze(Object.assign(new Error("private-event-canary@example.invalid"), { diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1) }));
  const records: DiagnosticRecord[] = [];
  const diagnostics: CoreEventDiagnosticOptions = { diagnosticDefinitions: [sourceDefinition], onDiagnostic(record, context) {
    equal(this, diagnostics); equal(Object.isFrozen(context), true); records.push(record);
  } };
  const literal = (code: string, detail: unknown) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  const boundary = (detail: unknown): void => {
    deepEqual(records[0], literal("core.events.boundary-failed", detail)); deepEqual(records.slice(1), sourceRecords);
    equal(records.length, 10); equal(JSON.stringify(records).includes("private-event-canary"), false); records.length = 0;
  };
  for (const value of ["", "Deal.Updated", "single"]) {
    const result = eventType(value, diagnostics); if (result.ok) throw new Error("Expected type rejection");
    equal(result.error.code, "EVENT_INVALID_TYPE"); deepEqual(result.error.params, { type: value });
    deepEqual(result.error.diagnosticRecord, literal("core.events.validation-rejected", { operation: "event-type", field: "type", reason: "invalid-format", effect: "rejected" }));
    deepEqual(records, [result.error.diagnosticRecord]); records.length = 0;
  }
  for (const value of [0, -1, 0.5, NaN, Infinity]) {
    const result = eventVersion(value, diagnostics); if (result.ok) throw new Error("Expected version rejection");
    equal(result.error.code, "EVENT_INVALID_VERSION"); deepEqual(result.error.params, { version: String(value) });
    deepEqual(result.error.diagnosticRecord, literal("core.events.validation-rejected", { operation: "event-version", field: "version", reason: Number.isInteger(value) ? "not-positive" : "not-integer", effect: "rejected" }));
    records.length = 0;
  }
  let cause = fresh();
  throws(() => eventType({ toString() { throw cause; } } as unknown as string, diagnostics), (error) => error === cause);
  boundary({ operation: "event-type", phase: "predicate", field: "type", reason: "threw", effect: "result-not-returned" });
  throws(() => eventVersion({ toString() { throw cause; } } as unknown as number, diagnostics), (error) => error === cause);
  deepEqual(records.shift(), literal("core.events.validation-rejected", { operation: "event-version", field: "version", reason: "not-integer", effect: "rejected" }));
  boundary({ operation: "event-version", phase: "parameter-formatting", field: "version", reason: "threw", effect: "result-not-returned" });
  const reads: string[] = [];
  eventEnvelope(new Proxy(event, { get(target, key, receiver) { reads.push(String(key)); return Reflect.get(target, key, receiver); } }), diagnostics);
  deepEqual(reads, ["id", "type", "version", "occurredAt", "tenantId", "tenantId", "correlationId", "correlationId", "causationId", "causationId", "payload"]);
  equal(records.length, 0);
  throws(() => eventEnvelope(Object.defineProperty({ ...event }, "payload", { get() { throw cause; } }), diagnostics), (error) => error === cause);
  boundary({ operation: "envelope", phase: "input-projection", field: "payload", reason: "threw", effect: "result-not-returned" });
  for (const declaration of [Object.defineProperty({}, "handlers", { get() { throw cause; } }), { handlers: { [Symbol.iterator]() { throw cause; } } }]) {
    throws(() => inMemoryEventBus(declaration as never, diagnostics), (error) => error === cause);
    boundary({ operation: "bus-construction", phase: "handler-declaration", field: "handlers", reason: "threw", effect: "bus-not-created" });
  }
  const bus = inMemoryEventBus({}, diagnostics);
  let mapCalls = 0, callbackCalls = 0;
  const mapped = [event];
  Object.defineProperty(mapped, "map", { value(callback: (event: EventEnvelope, index: number) => unknown) {
    equal(this, mapped); mapCalls++; callbackCalls++; callback(event, 4096); callbackCalls++; callback(event, 8192); throw cause;
  } });
  await rejects(bus.publish(mapped), (error) => error === cause);
  equal(mapCalls, 1); equal(callbackCalls, 2);
  boundary({ operation: "publish", phase: "batch-copy", field: "events", reason: "threw", effect: "publish-not-appended" });
  let calls = 0;
  const ordered: string[] = [];
  const badEvent = Object.defineProperty({ ...event }, "payload", { get() { ordered.push("payload"); throw cause; } });
  const argumentInput = [event]; Object.defineProperty(argumentInput, "map", { value() { return [badEvent]; } });
  const argumentHandler: EventHandler = { get handle(): EventHandler["handle"] { ordered.push("handle"); return function() { calls++; }; } };
  const failedArgument = await inMemoryEventBus({ handlers: [argumentHandler] }, diagnostics).publish(argumentInput);
  if (failedArgument.ok) throw new Error("Expected handler argument failure");
  equal(failedArgument.error.code, "EVENT_HANDLER_FAILED"); equal(failedArgument.error.cause, cause);
  deepEqual(failedArgument.error.diagnosticRecord, sourceRecords[0]); deepEqual(failedArgument.error.relatedDiagnosticRecords, sourceRecords.slice(1));
  deepEqual(ordered, ["handle", "payload"]); equal(calls, 0);
  boundary({ operation: "publish", phase: "handler-argument-copy", field: "payload", reason: "threw", effect: "publish-not-appended", handlerEffect: "not-invoked", eventOrdinal: 0, handlerOrdinal: 0 });
  for (const mode of ["selection", "throw", "reject"] as const) {
    cause = fresh();
    const handler: EventHandler = mode === "selection" ? Object.defineProperty({}, "handle", { get() { throw cause; } }) as EventHandler : { handle() {
      equal(this, handler); calls++; if (mode === "throw") throw cause; return Promise.reject(cause);
    } };
    const failedBus = inMemoryEventBus({ handlers: [handler] }, diagnostics);
    const result = await failedBus.publish([event]); if (result.ok) throw new Error("Expected handler failure");
    equal(result.error.cause, cause); deepEqual(result.error.details, { eventId: event.id, eventType: event.type, eventVersion: event.version });
    deepEqual(result.error.relatedDiagnosticRecords, sourceRecords.slice(1)); deepEqual(failedBus.publishedEvents(), []);
    boundary({ operation: "publish", phase: mode === "selection" ? "handler-selection" : mode === "throw" ? "handler-invocation" : "handler-completion", field: "handler", reason: mode === "reject" ? "rejected" : "threw", effect: "publish-not-appended", handlerEffect: mode === "selection" ? "not-invoked" : "unknown", eventOrdinal: 0, handlerOrdinal: 0 });
  }
  const effects: string[] = [];
  const second = { ...event, id: eventId("event-second") };
  const partial = inMemoryEventBus({ handlers: [{ handle(value) { effects.push(`first:${value.id}`); } }, { handle(value) { effects.push(`second:${value.id}`); if (value.id === second.id) throw cause; } }] }, diagnostics);
  const partialResult = await partial.publish([event, second, { ...event, id: eventId("never") }]); equal(partialResult.ok, false);
  deepEqual(effects, [`first:${event.id}`, `second:${event.id}`, `first:${second.id}`, `second:${second.id}`]); deepEqual(partial.publishedEvents(), []);
  boundary({ operation: "publish", phase: "handler-invocation", field: "handler", reason: "threw", effect: "publish-not-appended", handlerEffect: "unknown", eventOrdinal: 1, handlerOrdinal: 1 });
  let eventSteps = 0, eventHandled = 0;
  const eventIterationInput = [event];
  Object.defineProperty(eventIterationInput, "map", { value() { return { *[Symbol.iterator]() { eventSteps++; yield event; eventSteps++; throw cause; } }; } });
  const eventIterationBus = inMemoryEventBus({ handlers: [{ handle() { eventHandled++; } }] }, diagnostics);
  await rejects(eventIterationBus.publish(eventIterationInput), (error) => error === cause);
  equal(eventSteps, 2); equal(eventHandled, 1); deepEqual(eventIterationBus.publishedEvents(), []);
  boundary({ operation: "publish", phase: "event-iteration", field: "events", reason: "threw", effect: "publish-not-appended" });
  let handlerSteps = 0, handlerHandled = 0;
  const firstHandler: EventHandler = { handle() { handlerHandled++; } };
  const handlerIterationBus = inMemoryEventBus({ handlers: [firstHandler] }, diagnostics);
  const originalIterator = Array.prototype[Symbol.iterator];
  Array.prototype[Symbol.iterator] = function<T>(this: T[]): ArrayIterator<T> {
    if (this[0] !== firstHandler) return Reflect.apply(originalIterator, this, []) as ArrayIterator<T>;
    return (function* () { handlerSteps++; yield firstHandler as unknown as T; handlerSteps++; throw cause; })() as unknown as ArrayIterator<T>;
  };
  try { await rejects(handlerIterationBus.publish([event]), (error) => error === cause); }
  finally { Array.prototype[Symbol.iterator] = originalIterator; }
  equal(handlerSteps, 2); equal(handlerHandled, 1); deepEqual(handlerIterationBus.publishedEvents(), []);
  boundary({ operation: "publish", phase: "handler-iteration", field: "handlers", reason: "threw", effect: "publish-not-appended", eventOrdinal: 0 });
  let traversals = 0, handled = 0;
  const appendEvents = [event];
  const iterable = { *[Symbol.iterator]() { traversals++; yield event; if (traversals === 2) throw cause; } };
  Object.defineProperty(appendEvents, "map", { value() { return iterable; } });
  const appendBus = inMemoryEventBus({ handlers: [{ handle() { handled++; } }] }, diagnostics);
  await rejects(appendBus.publish(appendEvents), (error) => error === cause);
  equal(traversals, 2); equal(handled, 1); deepEqual(appendBus.publishedEvents(), []);
  boundary({ operation: "publish", phase: "published-append", field: "events", reason: "threw", effect: "append-outcome-unknown" });
  const snapshotBus = inMemoryEventBus({}, diagnostics);
  let snapshotReads = 0;
  const snapshotEvent = Object.defineProperty({ ...event }, "payload", { get() { snapshotReads++; throw cause; } });
  const snapshotInput = [event]; Object.defineProperty(snapshotInput, "map", { value() { return [snapshotEvent]; } });
  equal((await snapshotBus.publish(snapshotInput)).ok, true); equal(records.length, 0);
  throws(() => snapshotBus.publishedEvents(), (error) => error === cause); equal(snapshotReads, 1);
  boundary({ operation: "published-events", phase: "snapshot-copy", field: "payload", reason: "threw", effect: "snapshot-not-returned" });
  for (const raw of ["private-primitive-canary", Object.freeze(new Error("private-frozen-canary"))]) {
    await rejects(inMemoryEventBus({}, diagnostics).publish(Object.defineProperty([], "map", { get() { throw raw; } })), (error) => error === raw);
    equal(records.length, 1); deepEqual(records[0], literal("core.events.boundary-failed", { operation: "publish", phase: "batch-copy", field: "events", reason: "threw", effect: "publish-not-appended" })); records.length = 0;
  }
  let sourceReads = 0;
  const accessor = Object.defineProperty(new Error("private"), "diagnosticRecord", { get() { sourceReads++; throw cause; } });
  await rejects(bus.publish(Object.defineProperty([], "map", { get() { throw accessor; } })), (error) => error === accessor);
  equal(sourceReads, 0); equal(records.length, 2);
  deepEqual(records[1], literal("core.diagnostics.processing-failed", { reason: "evidence-inaccessible" })); records.length = 0;
  const unselected: DiagnosticRecord[] = [];
  const unavailable = inMemoryEventBus({}, { onDiagnostic(record) { unselected.push(record); } });
  await rejects(unavailable.publish(Object.defineProperty([], "map", { get() { throw cause; } })), (error) => error === cause);
  equal(unselected.length, 1);
  const malformed = Object.freeze(Object.assign(new Error("private-malformed"), { diagnosticRecord: { ...sourceRecords[0], detail: { secret: "private-malformed" } }, relatedDiagnosticRecords: sourceRecords.slice(1) }));
  const malformedResult = await inMemoryEventBus({ handlers: [{ handle() { throw malformed; } }] }, diagnostics).publish([event]);
  if (malformedResult.ok) throw new Error("Expected malformed-source handler failure");
  equal(malformedResult.error.diagnosticRecord?.code, "core.events.boundary-failed"); deepEqual(malformedResult.error.relatedDiagnosticRecords, sourceRecords.slice(1));
  equal(records.length, 10); deepEqual(records.slice(1, 9), sourceRecords.slice(1));
  deepEqual(records[9], literal("core.diagnostics.processing-failed", { reason: "evidence-rejected" }));
  equal(JSON.stringify(records).includes("private-malformed"), false); records.length = 0;
  for (const raw of ["private-handler-primitive", Object.freeze(new Error("private-handler-frozen"))]) {
    const result = await inMemoryEventBus({ handlers: [{ handle() { throw raw; } }] }, diagnostics).publish([event]);
    if (result.ok) throw new Error("Expected handler failure"); equal(result.error.cause, raw);
    deepEqual(result.error.diagnosticRecord, literal("core.events.boundary-failed", { operation: "publish", phase: "handler-invocation", field: "handler", reason: "threw", effect: "publish-not-appended", handlerEffect: "unknown", eventOrdinal: 0, handlerOrdinal: 0 }));
    equal(records.length, 1); records.length = 0;
  }
  const unhandled: unknown[] = [], listener = (error: unknown): void => { unhandled.push(error); };
  process.on("unhandledRejection", listener);
  try {
    for (const mode of ["throw", "native", "shadowed", "thenable", "getter"] as const) {
      let sinkCalls = 0, thenReads = 0;
      const options: CoreEventDiagnosticOptions = { diagnosticDefinitions: [sourceDefinition], onDiagnostic() {
        equal(this, options); sinkCalls++; if (mode === "throw") throw cause;
        if (mode === "thenable") return { then(_resolve: unknown, reject: (value: unknown) => void) { reject(cause); } };
        if (mode === "getter") return Object.defineProperty({}, "then", { get() { throw cause; } });
        const pending = Promise.reject(cause); if (mode === "shadowed") Object.defineProperty(pending, "then", { get() { thenReads++; throw cause; } }); return pending;
      } };
      await rejects(inMemoryEventBus({}, options).publish(Object.defineProperty([], "map", { get() { throw cause; } })), (error) => error === cause);
      equal(sinkCalls, 10); equal(thenReads, 0);
    }
    await new Promise<void>((resolve) => setImmediate(resolve)); deepEqual(unhandled, []);
  } finally { process.off("unhandledRejection", listener); }
}

main()
  .then(() => {
    console.log("packages/core events runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
