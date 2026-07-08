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
  type Queue,
  type QueueAttempt,
  type QueueDeadLetterMetadata,
  type QueueDelaySeconds,
  type QueueDelivery,
  type QueueError,
  type QueueErrorCode,
  type QueueHandler,
  type QueueMessage,
  type QueueMessageType,
  type QueueMessageVersion,
  type QueuePayload,
  type QueuePayloadValue,
  type QueueRetryMetadata,
  type QueueSendOptions,
} from "../src/queues/index";
import { correlationId, isOk, isoDateTime, type Result } from "../src/shared/index";
import { tenantId } from "../src/tenancy/index";

const typeResult: Result<QueueMessageType, QueueError> = queueMessageType("notifications.send-welcome-email");
const versionResult: Result<QueueMessageVersion, QueueError> = queueMessageVersion(1);
const delayResult: Result<QueueDelaySeconds, QueueError> = queueDelaySeconds(30);
const attemptResult: Result<QueueAttempt, QueueError> = queueAttempt(1);
const maxAttemptResult: Result<QueueAttempt, QueueError> = queueAttempt(3);
const deadLetterReasonResult = queueDeadLetterReason("max-attempts-exceeded");
const timestamp = isoDateTime("2026-07-07T12:00:00.000Z");
const nextRetryAt = isoDateTime("2026-07-07T12:01:00.000Z");
const acceptedCode: QueueErrorCode = "QUEUE_SEND_FAILED";
const acceptedError: QueueError = queueError({
  code: acceptedCode,
  defaultMessage: "Queue send failed.",
  messageKey: "queues.send.failed",
});
const payloadValue: QueuePayloadValue = {
  principalId: "principal-123",
  locale: "en-GB",
  metadata: { source: "signup", priority: 2, retryable: true },
};
const payload: QueuePayload = {
  principalId: "principal-123",
  locale: "en-GB",
};

if (
  !isOk(typeResult) ||
  !isOk(versionResult) ||
  !isOk(delayResult) ||
  !isOk(attemptResult) ||
  !isOk(maxAttemptResult) ||
  !isOk(deadLetterReasonResult) ||
  !isOk(timestamp) ||
  !isOk(nextRetryAt)
) {
  throw new Error("Expected valid test primitives.");
}

const retry: QueueRetryMetadata = queueRetryMetadata({
  attempt: attemptResult.value,
  maxAttempts: maxAttemptResult.value,
  nextRetryAt: nextRetryAt.value,
}).ok
  ? {
      attempt: attemptResult.value,
      maxAttempts: maxAttemptResult.value,
      nextRetryAt: nextRetryAt.value,
    }
  : { attempt: attemptResult.value };
const deadLetter: QueueDeadLetterMetadata = queueDeadLetterMetadata({
  reason: deadLetterReasonResult.value,
  failedAt: nextRetryAt.value,
  attempts: maxAttemptResult.value,
});
const message: QueueMessage<QueuePayload> = queueMessage({
  id: queueMessageId("queue-message-123"),
  type: typeResult.value,
  version: versionResult.value,
  enqueuedAt: timestamp.value,
  tenantId: tenantId("tenant-123"),
  correlationId: correlationId("request-123"),
  idempotencyKey: queueIdempotencyKey("welcome-email:principal-123"),
  messageGroupKey: queueMessageGroupKey("tenant-123"),
  payload,
});
const options: QueueSendOptions = queueSendOptions({ delaySeconds: delayResult.value });
const delivery: QueueDelivery<QueuePayload> = queueDelivery({
  message,
  receivedAt: timestamp.value,
  attempt: attemptResult.value,
  retry,
  deadLetter,
});
const handler: QueueHandler<QueueDelivery<QueuePayload>> = {
  handle: (_delivery) => undefined,
};
const queue: Queue<QueuePayload> = inMemoryQueue<QueuePayload>();
const noQueue: Queue = noopQueue;

void acceptedError;
void payloadValue;
void delivery;
void handler;
void queue;
void noQueue;

queue.send(message, options);
noQueue.send(message);
handler.handle(delivery);

// @ts-expect-error queue message types must be explicitly created and branded.
const invalidType: QueueMessageType = "notifications.send-welcome-email";
void invalidType;

// @ts-expect-error queue message versions must be explicitly created and branded.
const invalidVersion: QueueMessageVersion = 1;
void invalidVersion;

// @ts-expect-error queue delays must be explicitly created and branded.
const invalidDelay: QueueDelaySeconds = 30;
void invalidDelay;

// @ts-expect-error queue attempts must be explicitly created and branded.
const invalidAttempt: QueueAttempt = 1;
void invalidAttempt;

// @ts-expect-error queue payloads must stay plain and serializable.
const invalidPayload: QueuePayloadValue = new Date();
void invalidPayload;

queueMessage({
  // @ts-expect-error queue messages require a branded message id.
  id: "queue-message-123",
  type: typeResult.value,
  enqueuedAt: timestamp.value,
  payload,
});

queueMessage({
  id: queueMessageId("queue-message-123"),
  // @ts-expect-error queue messages require a branded message type.
  type: "notifications.send-welcome-email",
  enqueuedAt: timestamp.value,
  payload,
});

queueMessage({
  id: queueMessageId("queue-message-123"),
  type: typeResult.value,
  // @ts-expect-error queue message versions must be explicitly created and branded when supplied.
  version: 1,
  enqueuedAt: timestamp.value,
  payload,
});

queueMessage({
  id: queueMessageId("queue-message-123"),
  type: typeResult.value,
  enqueuedAt: timestamp.value,
  // @ts-expect-error queue idempotency key must be explicitly branded.
  idempotencyKey: "welcome-email:principal-123",
  payload,
});

queueSendOptions({
  // @ts-expect-error queue delay must be explicitly branded.
  delaySeconds: 30,
});

queueDelivery({
  message,
  receivedAt: timestamp.value,
  // @ts-expect-error queue delivery attempts must be explicitly branded.
  attempt: 1,
});

// @ts-expect-error queue error codes are constrained.
queueError({ code: "SQS_RECEIPT_HANDLE_FAILED", defaultMessage: "Provider failed." });
