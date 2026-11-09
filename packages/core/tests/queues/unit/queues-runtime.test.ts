import { deepEqual, equal, throws } from "node:assert/strict";
import {
  inMemoryQueue,
  noopQueue,
  queueAttempt,
  queueDeadLetterMetadata,
  queueDeadLetterReason,
  queueDelaySeconds,
  queueDelivery,
  queueError,
  queueIdempotencyKey,
  queueMessage,
  queueMessageGroupKey,
  queueMessageId,
  queueMessageType,
  queueMessageVersion,
  queueRetryMetadata,
  queueSendOptions,
  coreQueueValidationDiagnosticRecord,
  coreQueueBoundaryDiagnosticRecord,
  coreQueueBoundaryDiagnostic,
  coreQueueReceiveReductionDiagnosticRecord,
  observeCoreQueueDiagnostic,
  selectCoreQueueDiagnosticEvidence,
  type CoreQueueValidationDetail,
  type CoreQueueDiagnosticContext,
  type QueueMessage,
} from "../../../src/queues/index";
import { diagnosticProcessingRecord, diagnosticDescriptor, createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "../../../src/diagnostics/index";
import { spanId, traceContext, traceId } from "../../../src/monitoring/index";
import { causationId, correlationId, isErr, isOk, isoDateTime } from "../../../src/shared/index";
import { tenantId } from "../../../src/tenancy/index";

async function main(): Promise<void> {
  const validType = queueMessageType("notifications.send-welcome-email");
  equal(isOk(validType), true);
  if (!isOk(validType)) {
    throw new Error("Expected queue message type to be valid.");
  }
  equal(validType.value, "notifications.send-welcome-email");

  const invalidType = queueMessageType("Send Welcome Email");
  equal(isErr(invalidType), true);
  if (!isErr(invalidType)) {
    throw new Error("Expected queue message type to be invalid.");
  }
  equal(invalidType.error.code, "QUEUE_INVALID_TYPE");
  equal(invalidType.error.messageKey, "queues.type.invalid");

  const validVersion = queueMessageVersion(1);
  equal(isOk(validVersion), true);
  if (!isOk(validVersion)) {
    throw new Error("Expected queue message version to be valid.");
  }
  equal(validVersion.value, 1);

  const invalidVersion = queueMessageVersion(0);
  equal(isErr(invalidVersion), true);
  if (!isErr(invalidVersion)) {
    throw new Error("Expected queue message version to be invalid.");
  }
  equal(invalidVersion.error.code, "QUEUE_INVALID_VERSION");
  equal(invalidVersion.error.messageKey, "queues.version.invalid");

  const validDelay = queueDelaySeconds(30);
  equal(isOk(validDelay), true);
  if (!isOk(validDelay)) {
    throw new Error("Expected queue delay to be valid.");
  }

  const invalidDelay = queueDelaySeconds(-1);
  equal(isErr(invalidDelay), true);
  if (!isErr(invalidDelay)) {
    throw new Error("Expected queue delay to be invalid.");
  }
  equal(invalidDelay.error.code, "QUEUE_INVALID_DELAY");
  equal(invalidDelay.error.messageKey, "queues.delay.invalid");

  const firstAttempt = queueAttempt(1);
  const maxAttempts = queueAttempt(3);
  equal(isOk(firstAttempt), true);
  equal(isOk(maxAttempts), true);
  if (!isOk(firstAttempt) || !isOk(maxAttempts)) {
    throw new Error("Expected queue attempts to be valid.");
  }

  const invalidAttempt = queueAttempt(0);
  equal(isErr(invalidAttempt), true);
  if (!isErr(invalidAttempt)) {
    throw new Error("Expected queue attempt to be invalid.");
  }
  equal(invalidAttempt.error.code, "QUEUE_INVALID_ATTEMPT");
  equal(invalidAttempt.error.messageKey, "queues.attempt.invalid");

  const enqueuedAt = isoDateTime("2026-07-07T12:00:00.000Z");
  const receivedAt = isoDateTime("2026-07-07T12:00:10.000Z");
  const nextRetryAt = isoDateTime("2026-07-07T12:01:00.000Z");
  equal(isOk(enqueuedAt), true);
  equal(isOk(receivedAt), true);
  equal(isOk(nextRetryAt), true);
  if (!isOk(enqueuedAt) || !isOk(receivedAt) || !isOk(nextRetryAt)) {
    throw new Error("Expected queue timestamps to be valid.");
  }

  const payload = {
    principalId: "principal-123",
    locale: "en-GB",
    metadata: { source: "signup", priority: 2 },
  };
  const message = queueMessage({
    id: queueMessageId("queue-message-123"),
    type: validType.value,
    version: validVersion.value,
    enqueuedAt: enqueuedAt.value,
    tenantId: tenantId("tenant-123"),
    correlationId: correlationId("request-123"),
    causationId: causationId("event-123"),
    traceParent: traceContext({
      traceId: traceId("trace-123"),
      spanId: spanId("span-123"),
    }),
    idempotencyKey: queueIdempotencyKey("welcome-email:principal-123"),
    messageGroupKey: queueMessageGroupKey("tenant-123"),
    payload,
  });

  deepEqual(message, {
    id: "queue-message-123",
    type: "notifications.send-welcome-email",
    version: 1,
    enqueuedAt: "2026-07-07T12:00:00.000Z",
    tenantId: "tenant-123",
    correlationId: "request-123",
    causationId: "event-123",
    traceParent: {
      traceId: "trace-123",
      spanId: "span-123",
    },
    idempotencyKey: "welcome-email:principal-123",
    messageGroupKey: "tenant-123",
    payload: {
      principalId: "principal-123",
      locale: "en-GB",
      metadata: { source: "signup", priority: 2 },
    },
  });

  payload.metadata.source = "mutated";
  deepEqual(message.payload, {
    principalId: "principal-123",
    locale: "en-GB",
    metadata: { source: "signup", priority: 2 },
  });

  const retry = queueRetryMetadata({
    attempt: firstAttempt.value,
    maxAttempts: maxAttempts.value,
    nextRetryAt: nextRetryAt.value,
  });
  equal(isOk(retry), true);
  if (!isOk(retry)) {
    throw new Error("Expected retry metadata to be valid.");
  }

  const exceededRetry = queueRetryMetadata({
    attempt: maxAttempts.value,
    maxAttempts: firstAttempt.value,
  });
  equal(isErr(exceededRetry), true);
  if (!isErr(exceededRetry)) {
    throw new Error("Expected retry metadata to reject attempt beyond max.");
  }
  equal(exceededRetry.error.code, "QUEUE_INVALID_ATTEMPT");
  equal(exceededRetry.error.messageKey, "queues.attempt.exceeds_max");

  const deadLetterReason = queueDeadLetterReason("max-attempts-exceeded");
  equal(isOk(deadLetterReason), true);
  if (!isOk(deadLetterReason)) {
    throw new Error("Expected dead-letter reason to be valid.");
  }

  const invalidDeadLetterReason = queueDeadLetterReason("Max Attempts Exceeded");
  equal(isErr(invalidDeadLetterReason), true);
  if (!isErr(invalidDeadLetterReason)) {
    throw new Error("Expected dead-letter reason to be invalid.");
  }
  equal(invalidDeadLetterReason.error.code, "QUEUE_INVALID_DEAD_LETTER_REASON");
  equal(invalidDeadLetterReason.error.messageKey, "queues.dead_letter.reason.invalid");

  const deadLetter = queueDeadLetterMetadata({
    reason: deadLetterReason.value,
    failedAt: nextRetryAt.value,
    attempts: maxAttempts.value,
  });
  const delivery = queueDelivery({
    message,
    receivedAt: receivedAt.value,
    attempt: firstAttempt.value,
    retry: retry.value,
  });
  deepEqual(delivery.message, message);
  deepEqual(delivery.retry, retry.value);
  equal(delivery.deadLetter, undefined);

  const deadLetterDelivery = queueDelivery({
    message,
    receivedAt: receivedAt.value,
    attempt: maxAttempts.value,
    deadLetter,
  });
  deepEqual(deadLetterDelivery.deadLetter, deadLetter);
  equal(deadLetterDelivery.retry, undefined);

  throws(
    () =>
      queueDelivery({
        message,
        receivedAt: receivedAt.value,
        attempt: firstAttempt.value,
        retry: retry.value,
        deadLetter,
      } as never),
    /cannot be both retryable and dead-lettered/,
  );

  const explicitError = queueError({
    code: "QUEUE_SEND_FAILED",
    defaultMessage: "Queue send failed.",
    messageKey: "queues.send.failed",
    diagnostic: diagnosticDescriptor({
      failureKind: "dependency_unavailable",
      failureSource: "provider",
      severity: "error",
      recovery: "automation_retryable",
      action: "retry",
    }),
  });
  equal(explicitError.code, "QUEUE_SEND_FAILED");
  equal(explicitError.messageKey, "queues.send.failed");
  equal(explicitError.diagnostic?.retryable, true);

  const queue = inMemoryQueue<typeof message.payload>();
  const options = queueSendOptions({ delaySeconds: validDelay.value });
  const sendResult = await queue.send(message, options);
  equal(isOk(sendResult), true);
  deepEqual(queue.acceptedMessages(), [message]);
  deepEqual(queue.acceptedSends(), [{ message, options }]);

  const stored = queue.acceptedMessages() as QueueMessage<typeof message.payload>[];
  const storedPayload = stored[0]?.payload;
  if (storedPayload === undefined) {
    throw new Error("Expected stored queue payload.");
  }
  storedPayload.metadata.source = "changed";
  deepEqual(queue.acceptedMessages()[0]?.payload, {
    principalId: "principal-123",
    locale: "en-GB",
    metadata: { source: "signup", priority: 2 },
  });

  const invalidPayloadMessage = () =>
    queueMessage({
      id: queueMessageId("queue-message-invalid-payload"),
      type: validType.value,
      enqueuedAt: enqueuedAt.value,
      payload: { score: Number.NaN },
    });
  throws(invalidPayloadMessage, /finite numbers/);

  const invalidRuntimePayloadMessage = () =>
    queueMessage({
      id: queueMessageId("queue-message-invalid-runtime-payload"),
      type: validType.value,
      enqueuedAt: enqueuedAt.value,
      payload: { when: new Date() as never },
    });
  throws(invalidRuntimePayloadMessage, /plain objects/);

  throws(() => queueIdempotencyKey(""), /must not be empty/);
  throws(() => queueMessageGroupKey(""), /must not be empty/);

  const noopResult = await noopQueue.send(message);
  equal(isOk(noopResult), true);

  const own = coreQueueBoundaryDiagnosticRecord({ operation: "send", boundary: "invocation", reason: "rejected", effect: "unknown" });
  deepEqual(own, { schema: "core/diagnostic-record/v1", code: "core.queue.boundary-failed", definitionVersion: 1,
    detail: { operation: "send", boundary: "invocation", reason: "rejected", effect: "unknown" } });
  const nativeOwn = coreQueueBoundaryDiagnosticRecord({ operation: "send", boundary: "invocation", reason: "rejected", effect: "unknown", native: { codeAvailability: "recognized", condition: "request-throttled" } });
  deepEqual(nativeOwn.detail.native, { codeAvailability: "recognized", condition: "request-throttled" });
  deepEqual(coreQueueBoundaryDiagnostic.classification, { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation", retryable: false, userCorrectable: false });
  throws(() => coreQueueBoundaryDiagnosticRecord({ ...own.detail, native: { codeAvailability: "recognized", condition: "AccessDeniedException" } } as never), /CORE_QUEUE_DIAGNOSTIC_INVALID/);
  const rejection = (result: { ok: boolean; error?: unknown }, field: CoreQueueValidationDetail["field"], reason: CoreQueueValidationDetail["reason"]): void => {
    equal(result.ok, false);
    deepEqual((result.error as { diagnosticRecord: unknown }).diagnosticRecord, coreQueueValidationDiagnosticRecord({ operation: "validate", field, reason, effect: "rejected" }));
  };
  rejection(queueMessageType("PRIVATE_QUEUE_CANARY"), "message-type", "invalid-format");
  rejection(queueDeadLetterReason("PRIVATE_QUEUE_CANARY"), "dead-letter-reason", "invalid-format");
  for (const value of [NaN, Infinity, 0.5]) {
    rejection(queueMessageVersion(value), "message-version", "not-integer");
    rejection(queueDelaySeconds(value), "delay", "not-integer");
    rejection(queueAttempt(value), "attempt", "not-integer");
  }
  for (const value of [0, -1]) { rejection(queueMessageVersion(value), "message-version", "not-positive"); rejection(queueAttempt(value), "attempt", "not-positive"); }
  rejection(queueDelaySeconds(-1), "delay", "negative");
  let retryReads: string[] = [];
  const exceeded = queueRetryMetadata({ get attempt() { retryReads.push("attempt"); return maxAttempts.value; }, get maxAttempts() { retryReads.push("max"); return firstAttempt.value; } });
  rejection(exceeded, "retry-attempt", "exceeds-maximum-attempt");
  deepEqual(retryReads, ["max", "attempt", "max", "attempt", "max"]);
  for (const [construct, field] of [[queueIdempotencyKey, "idempotency-key"], [queueMessageGroupKey, "message-group-key"]] as const) {
    throws(() => construct(""), (error: unknown) => { equal(error instanceof TypeError, true); deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord,
      coreQueueValidationDiagnosticRecord({ operation: "validate", field, reason: "empty", effect: "rejected" })); return true; });
  }
  let dispositionReads: string[] = [];
  throws(() => queueDelivery({ message, receivedAt: receivedAt.value, attempt: firstAttempt.value,
    get retry() { dispositionReads.push("retry"); return retry.value; }, get deadLetter() { dispositionReads.push("dead"); return deadLetter; } } as never),
  (error: unknown) => { deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, coreQueueValidationDiagnosticRecord({ operation: "validate", field: "delivery-disposition", reason: "conflicting", effect: "rejected" })); return true; });
  deepEqual(dispositionReads, ["retry", "dead"]);
  const raw = Object.freeze(new Error("PRIVATE_QUEUE_CANARY"));
  throws(() => queueIdempotencyKey(Object.defineProperty({}, "length", { get() { throw raw; } }) as never), (error) => error === raw);

  const source = Array.from({ length: 9 }, (_, index) => coreQueueValidationDiagnosticRecord({ operation: "validate", field: "attempt", reason: index === 0 ? "not-integer" : "not-positive", effect: "rejected" }));
  const sourceError = Object.freeze({ diagnosticRecord: source[0], relatedDiagnosticRecords: source.slice(1), message: "PRIVATE_QUEUE_CANARY" });
  const seen: DiagnosticRecord[] = [];
  const contexts: CoreQueueDiagnosticContext[] = [];
  const owner = { onDiagnostic(record: DiagnosticRecord, context: CoreQueueDiagnosticContext) { equal(this, owner); seen.push(record); contexts.push(context); } };
  deepEqual(observeCoreQueueDiagnostic(owner, own, sourceError), { diagnosticRecord: source[0], relatedDiagnosticRecords: source.slice(1) });
  deepEqual(seen, [own, ...source]);
  equal(contexts.length, 10); contexts.forEach((context) => { equal(context, contexts[0]); deepEqual(context, { operation: "send", boundary: "invocation" }); });
  deepEqual(queueError({ code: "QUEUE_SEND_FAILED", defaultMessage: "Legacy.", diagnosticRecord: source[0]!, relatedDiagnosticRecords: source.slice(1) }).relatedDiagnosticRecords, source.slice(1));
  const definition = defineDiagnostic({ code: "queue-fixture.selected", version: 1, classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" }, detail: { type: "object", properties: {} } } as const);
  const selected = createDiagnosticRecord(definition, {}); if (!selected.ok) throw new Error("Fixture invalid");
  deepEqual(selectCoreQueueDiagnosticEvidence(undefined, { diagnosticRecord: selected.value }), {});
  equal(selectCoreQueueDiagnosticEvidence({ diagnosticDefinitions: [definition] }, { diagnosticRecord: selected.value }).diagnosticRecord?.code, definition.code);
  let accessorReads = 0;
  deepEqual(selectCoreQueueDiagnosticEvidence(undefined, Object.defineProperty({}, "diagnosticRecord", { get() { accessorReads++; throw raw; } })), {}); equal(accessorReads, 0);
  for (const cause of [0, "PRIVATE_QUEUE_CANARY", raw, Object.freeze({ name: "AccessDenied" })]) deepEqual(selectCoreQueueDiagnosticEvidence(undefined, cause), {});
  for (const onDiagnostic of [() => { throw raw; }, async () => { throw raw; }, () => Object.defineProperty(Promise.reject(raw), "then", { value: () => { throw raw; } }), () => ({ then(_resolve: unknown, reject: (reason: unknown) => void) { reject(raw); } })]) observeCoreQueueDiagnostic({ onDiagnostic }, own, sourceError);
  observeCoreQueueDiagnostic(Object.defineProperty({}, "onDiagnostic", { get() { throw raw; } }), own, sourceError);
  deepEqual(selectCoreQueueDiagnosticEvidence(Object.defineProperty({}, "diagnosticDefinitions", { get() { throw raw; } }), sourceError), { diagnosticRecord: source[0], relatedDiagnosticRecords: source.slice(1) });
  const reduction = coreQueueReceiveReductionDiagnosticRecord({ operation: "receive", issues: [{ field: "receive-count", reason: "not-positive", reduction: "count-one" }], truncated: false, effect: "reduction-observed" });
  const diagnosticModule = require("../../../src/queues/diagnostics") as Record<string, unknown>;
  const originalBuilder = Object.getOwnPropertyDescriptor(diagnosticModule, "coreQueueValidationDiagnosticRecord")!;
  for (const failure of ["throw", "undefined"] as const) {
    try {
      Object.defineProperty(diagnosticModule, "coreQueueValidationDiagnosticRecord", { ...originalBuilder, value: () => { if (failure === "throw") throw raw; return undefined; } });
      const result = queueMessageVersion(0);
      equal(result.ok, false);
      if (result.ok) throw new Error("Expected original queue validation failure");
      equal(result.error.code, "QUEUE_INVALID_VERSION");
      deepEqual(result.error.diagnosticRecord, diagnosticProcessingRecord(failure === "throw" ? "construction-threw" : "construction-rejected"));
    } finally { Object.defineProperty(diagnosticModule, "coreQueueValidationDiagnosticRecord", originalBuilder); }
  }
  seen.length = 0; contexts.length = 0;
  observeCoreQueueDiagnostic(owner, diagnosticProcessingRecord("construction-threw"), sourceError, { operation: "send", boundary: "invocation" });
  deepEqual(seen, [diagnosticProcessingRecord("construction-threw"), ...source]);
  contexts.forEach(context => deepEqual(context, { operation: "send", boundary: "invocation" }));
  seen.length = 0;
  observeCoreQueueDiagnostic(owner, own, Object.defineProperty({ relatedDiagnosticRecords: source.slice(1) }, "diagnosticRecord", { get() { accessorReads++; throw raw; } }));
  deepEqual(seen, [own, ...source.slice(1), diagnosticProcessingRecord("evidence-inaccessible")]);
  equal(accessorReads, 0);
  equal(reduction.code, "core.queue.receive-reduced"); equal(JSON.stringify([...seen, reduction]).includes("PRIVATE_QUEUE_CANARY"), false);
  await Promise.resolve();
}

main()
  .then(() => {
    console.log("packages/core queues runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
