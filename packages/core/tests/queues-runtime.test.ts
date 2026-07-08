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
  queueRetryMetadata,
  queueSendOptions,
  type QueueMessage,
} from "../src/queues/index";
import { correlationId, isErr, isOk, isoDateTime } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

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
    enqueuedAt: enqueuedAt.value,
    tenantId: tenantId("tenant-123"),
    correlationId: correlationId("request-123"),
    idempotencyKey: queueIdempotencyKey("welcome-email:principal-123"),
    messageGroupKey: queueMessageGroupKey("tenant-123"),
    payload,
  });

  deepEqual(message, {
    id: "queue-message-123",
    type: "notifications.send-welcome-email",
    enqueuedAt: "2026-07-07T12:00:00.000Z",
    tenantId: "tenant-123",
    correlationId: "request-123",
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
    deadLetter,
  });
  deepEqual(delivery.message, message);
  deepEqual(delivery.retry, retry.value);
  deepEqual(delivery.deadLetter, deadLetter);

  const explicitError = queueError({
    code: "QUEUE_SEND_FAILED",
    defaultMessage: "Queue send failed.",
    messageKey: "queues.send.failed",
  });
  equal(explicitError.code, "QUEUE_SEND_FAILED");
  equal(explicitError.messageKey, "queues.send.failed");

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
}

main()
  .then(() => {
    console.log("packages/core queues runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
