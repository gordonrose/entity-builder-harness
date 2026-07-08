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

export type QueueMessageId = EntityId<"QueueMessageId">;
export type QueueMessageType = Brand<string, "QueueMessageType">;
export type QueueMessageVersion = Brand<number, "QueueMessageVersion">;
export type QueueDelaySeconds = Brand<number, "QueueDelaySeconds">;
export type QueueAttempt = Brand<number, "QueueAttempt">;
export type QueueIdempotencyKey = Brand<string, "QueueIdempotencyKey">;
export type QueueMessageGroupKey = Brand<string, "QueueMessageGroupKey">;
export type QueueDeadLetterReason = Brand<string, "QueueDeadLetterReason">;
export type QueuePayloadValue = JsonValue;
export type QueuePayload = Readonly<Record<string, QueuePayloadValue>>;

export type QueueErrorCode =
  | "QUEUE_DEAD_LETTERED"
  | "QUEUE_HANDLER_FAILED"
  | "QUEUE_INVALID_ATTEMPT"
  | "QUEUE_INVALID_DEAD_LETTER_REASON"
  | "QUEUE_INVALID_DELAY"
  | "QUEUE_INVALID_TYPE"
  | "QUEUE_INVALID_VERSION"
  | "QUEUE_SEND_FAILED"
  | "QUEUE_UNAVAILABLE";

export interface QueueError extends CoreError {
  readonly code: QueueErrorCode;
}

export interface QueueMessage<TPayload extends QueuePayloadValue = QueuePayload> {
  readonly id: QueueMessageId;
  readonly type: QueueMessageType;
  readonly version: QueueMessageVersion;
  readonly enqueuedAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly idempotencyKey?: QueueIdempotencyKey;
  readonly messageGroupKey?: QueueMessageGroupKey;
  readonly payload: TPayload;
}

export interface QueueSendOptions {
  readonly delaySeconds?: QueueDelaySeconds;
}

export interface QueueRetryMetadata {
  readonly attempt: QueueAttempt;
  readonly maxAttempts?: QueueAttempt;
  readonly nextRetryAt?: ISODateTime;
}

export interface QueueDeadLetterMetadata {
  readonly reason: QueueDeadLetterReason;
  readonly failedAt: ISODateTime;
  readonly attempts: QueueAttempt;
}

export interface QueueDelivery<TPayload extends QueuePayloadValue = QueuePayload> {
  readonly message: QueueMessage<TPayload>;
  readonly receivedAt: ISODateTime;
  readonly attempt: QueueAttempt;
  readonly retry?: QueueRetryMetadata;
  readonly deadLetter?: QueueDeadLetterMetadata;
}

export interface QueueHandler<TDelivery extends QueueDelivery = QueueDelivery> {
  handle(delivery: TDelivery): Promise<void> | void;
}

export interface Queue<TPayload extends QueuePayloadValue = QueuePayload> {
  send(message: QueueMessage<TPayload>, options?: QueueSendOptions): Promise<Result<void, QueueError>>;
}

export interface QueueSend<TPayload extends QueuePayloadValue = QueuePayload> {
  readonly message: QueueMessage<TPayload>;
  readonly options?: QueueSendOptions;
}

export interface InMemoryQueue<TPayload extends QueuePayloadValue = QueuePayload> extends Queue<TPayload> {
  acceptedSends(): readonly QueueSend<TPayload>[];
  acceptedMessages(): readonly QueueMessage<TPayload>[];
}

export const currentQueueMessageVersion: QueueMessageVersion = brand<number, "QueueMessageVersion">(1);

export function queueMessageId(value: string): QueueMessageId {
  return entityId<"QueueMessageId">(value);
}

export function queueMessageType(value: string): Result<QueueMessageType, QueueError> {
  if (!messageTypePattern.test(value)) {
    return err(
      queueError({
        code: "QUEUE_INVALID_TYPE",
        defaultMessage: "Queue message type must use dot-separated lowercase segments.",
        messageKey: "queues.type.invalid",
        params: { type: value },
      }),
    );
  }

  return ok(brand<string, "QueueMessageType">(value));
}

export function queueMessageVersion(value: number): Result<QueueMessageVersion, QueueError> {
  if (!Number.isInteger(value) || value <= 0) {
    return err(
      queueError({
        code: "QUEUE_INVALID_VERSION",
        defaultMessage: "Queue message version must be a positive integer.",
        messageKey: "queues.version.invalid",
        params: { version: String(value) },
      }),
    );
  }

  return ok(brand<number, "QueueMessageVersion">(value));
}

export function queueDelaySeconds(value: number): Result<QueueDelaySeconds, QueueError> {
  if (!Number.isInteger(value) || value < 0) {
    return err(
      queueError({
        code: "QUEUE_INVALID_DELAY",
        defaultMessage: "Queue delay must be a non-negative integer number of seconds.",
        messageKey: "queues.delay.invalid",
        params: { delaySeconds: String(value) },
      }),
    );
  }

  return ok(brand<number, "QueueDelaySeconds">(value));
}

export function queueAttempt(value: number): Result<QueueAttempt, QueueError> {
  if (!Number.isInteger(value) || value <= 0) {
    return err(
      queueError({
        code: "QUEUE_INVALID_ATTEMPT",
        defaultMessage: "Queue attempt must be a positive integer.",
        messageKey: "queues.attempt.invalid",
        params: { attempt: String(value) },
      }),
    );
  }

  return ok(brand<number, "QueueAttempt">(value));
}

export function queueIdempotencyKey(value: string): QueueIdempotencyKey {
  return brand<string, "QueueIdempotencyKey">(requireNonEmpty(value, "Queue idempotency key"));
}

export function queueMessageGroupKey(value: string): QueueMessageGroupKey {
  return brand<string, "QueueMessageGroupKey">(requireNonEmpty(value, "Queue message group key"));
}

export function queueDeadLetterReason(value: string): Result<QueueDeadLetterReason, QueueError> {
  if (!deadLetterReasonPattern.test(value)) {
    return err(
      queueError({
        code: "QUEUE_INVALID_DEAD_LETTER_REASON",
        defaultMessage: "Queue dead-letter reason must use lowercase segments.",
        messageKey: "queues.dead_letter.reason.invalid",
        params: { reason: value },
      }),
    );
  }

  return ok(brand<string, "QueueDeadLetterReason">(value));
}

export function queueError(input: {
  readonly code: QueueErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly details?: Readonly<Record<string, unknown>>;
}): QueueError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
}

export function queueMessage<TPayload extends QueuePayloadValue>(input: {
  readonly id: QueueMessageId;
  readonly type: QueueMessageType;
  readonly version?: QueueMessageVersion;
  readonly enqueuedAt: ISODateTime;
  readonly tenantId?: TenantId;
  readonly correlationId?: CorrelationId;
  readonly idempotencyKey?: QueueIdempotencyKey;
  readonly messageGroupKey?: QueueMessageGroupKey;
  readonly payload: TPayload;
}): QueueMessage<TPayload> {
  return {
    id: input.id,
    type: input.type,
    version: input.version ?? currentQueueMessageVersion,
    enqueuedAt: input.enqueuedAt,
    ...(input.tenantId === undefined ? {} : { tenantId: input.tenantId }),
    ...(input.correlationId === undefined ? {} : { correlationId: input.correlationId }),
    ...(input.idempotencyKey === undefined ? {} : { idempotencyKey: input.idempotencyKey }),
    ...(input.messageGroupKey === undefined ? {} : { messageGroupKey: input.messageGroupKey }),
    payload: copyQueuePayloadValue(input.payload) as TPayload,
  };
}

export function queueSendOptions(input: {
  readonly delaySeconds?: QueueDelaySeconds;
} = {}): QueueSendOptions {
  return {
    ...(input.delaySeconds === undefined ? {} : { delaySeconds: input.delaySeconds }),
  };
}

export function queueRetryMetadata(input: {
  readonly attempt: QueueAttempt;
  readonly maxAttempts?: QueueAttempt;
  readonly nextRetryAt?: ISODateTime;
}): Result<QueueRetryMetadata, QueueError> {
  if (input.maxAttempts !== undefined && input.attempt > input.maxAttempts) {
    return err(
      queueError({
        code: "QUEUE_INVALID_ATTEMPT",
        defaultMessage: "Queue attempt must not exceed max attempts.",
        messageKey: "queues.attempt.exceeds_max",
        params: {
          attempt: String(input.attempt),
          maxAttempts: String(input.maxAttempts),
        },
      }),
    );
  }

  return ok({
    attempt: input.attempt,
    ...(input.maxAttempts === undefined ? {} : { maxAttempts: input.maxAttempts }),
    ...(input.nextRetryAt === undefined ? {} : { nextRetryAt: input.nextRetryAt }),
  });
}

export function queueDeadLetterMetadata(input: {
  readonly reason: QueueDeadLetterReason;
  readonly failedAt: ISODateTime;
  readonly attempts: QueueAttempt;
}): QueueDeadLetterMetadata {
  return {
    reason: input.reason,
    failedAt: input.failedAt,
    attempts: input.attempts,
  };
}

export function queueDelivery<TPayload extends QueuePayloadValue>(input: {
  readonly message: QueueMessage<TPayload>;
  readonly receivedAt: ISODateTime;
  readonly attempt: QueueAttempt;
  readonly retry?: QueueRetryMetadata;
  readonly deadLetter?: QueueDeadLetterMetadata;
}): QueueDelivery<TPayload> {
  return {
    message: copyQueueMessage(input.message),
    receivedAt: input.receivedAt,
    attempt: input.attempt,
    ...(input.retry === undefined ? {} : { retry: { ...input.retry } }),
    ...(input.deadLetter === undefined ? {} : { deadLetter: { ...input.deadLetter } }),
  };
}

export function inMemoryQueue<TPayload extends QueuePayloadValue = QueuePayload>(): InMemoryQueue<TPayload> {
  const accepted: QueueSend<TPayload>[] = [];

  return {
    async send(message, options = {}) {
      accepted.push({
        message: copyQueueMessage(message),
        options: copyQueueSendOptions(options),
      });
      return ok(undefined);
    },

    acceptedSends() {
      return accepted.map(copyQueueSend);
    },

    acceptedMessages() {
      return accepted.map((send) => copyQueueMessage(send.message));
    },
  };
}

export const noopQueue: Queue = {
  send: async () => ok(undefined),
};

const messageTypePattern = /^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$/;
const deadLetterReasonPattern = /^[a-z][a-z0-9-]*(?:[._-][a-z0-9]+)*$/;

function copyQueueSend<TPayload extends QueuePayloadValue>(send: QueueSend<TPayload>): QueueSend<TPayload> {
  return {
    message: copyQueueMessage(send.message),
    ...(send.options === undefined ? {} : { options: copyQueueSendOptions(send.options) }),
  };
}

function copyQueueMessage<TPayload extends QueuePayloadValue>(message: QueueMessage<TPayload>): QueueMessage<TPayload> {
  return queueMessage(message);
}

function copyQueueSendOptions(options: QueueSendOptions): QueueSendOptions {
  return queueSendOptions(options);
}

function copyQueuePayloadValue(value: QueuePayloadValue): QueuePayloadValue {
  return copyJsonValue(value, "queue payload");
}

function requireNonEmpty(value: string, label: string): string {
  if (value.length === 0) {
    throw new TypeError(`${label} must not be empty.`);
  }

  return value;
}
