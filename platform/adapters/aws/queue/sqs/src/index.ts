import {
  ChangeMessageVisibilityCommand,
  DeleteMessageCommand,
  ReceiveMessageCommand,
  SQSClient,
} from "@aws-sdk/client-sqs";
import {
  correlationId,
  isoDateTime,
  queueIdempotencyKey,
  queueMessage,
  queueMessageId,
  queueMessageType,
  queueMessageVersion,
  tenantId,
  type JsonValue,
  type QueueMessage,
  type QueuePayload,
} from "@kanbien/core";

export interface PlatformSqsWorkerQueue {
  receive(): Promise<PlatformSqsReceiveResult>;
  acknowledge(receiptHandle: string): Promise<void>;
  release(receiptHandle: string): Promise<void>;
}

export type PlatformSqsReceiveResult =
  | { readonly kind: "empty" }
  | {
      readonly kind: "delivery";
      readonly receiptHandle: string;
      readonly receiveCount: number;
      readonly message: QueueMessage;
    }
  | {
      readonly kind: "invalid";
      readonly receiptHandle: string;
      readonly receiveCount: number;
      readonly error: PlatformSqsWorkerQueueError;
    };

export interface PlatformSqsWorkerQueueError {
  readonly code:
    | "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID"
    | "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID"
    | "PLATFORM_ADAPTER_AWS_SQS_OPERATION_FAILED";
  readonly defaultMessage: string;
  readonly details?: Readonly<{ readonly path: string; readonly reason: string }>;
}

export interface PlatformSqsCommandClient {
  send(command: unknown): Promise<unknown>;
}

export interface PlatformSqsWorkerQueueOptions {
  readonly queueUrl: string;
  readonly waitTimeSeconds: number;
  readonly visibilityTimeoutSeconds: number;
  readonly client: PlatformSqsCommandClient;
}

export interface AwsSdkPlatformSqsWorkerQueueOptions {
  readonly queueUrl: string;
  readonly region: string;
  readonly waitTimeSeconds: number;
  readonly visibilityTimeoutSeconds: number;
}

export const adapterMetadata = {
  provider: "aws",
  capability: "queue",
  implementation: "sqs",
  packageName: "@kanbien/platform-adapter-aws-queue-sqs",
} as const;

export function createPlatformSqsWorkerQueue(
  options: PlatformSqsWorkerQueueOptions,
): PlatformSqsWorkerQueue {
  assertNonEmpty("queueUrl", options.queueUrl);
  assertWholeNumberInRange("waitTimeSeconds", options.waitTimeSeconds, 0, 20);
  assertWholeNumberInRange("visibilityTimeoutSeconds", options.visibilityTimeoutSeconds, 0, 43_200);

  return {
    receive: async () => {
      try {
        const response = await options.client.send(new ReceiveMessageCommand({
          QueueUrl: options.queueUrl,
          MaxNumberOfMessages: 1,
          WaitTimeSeconds: options.waitTimeSeconds,
          VisibilityTimeout: options.visibilityTimeoutSeconds,
          MessageSystemAttributeNames: ["ApproximateReceiveCount"],
        }));
        const message = firstSqsMessage(response);
        if (message === undefined) return { kind: "empty" };
        if (message.receiptHandle === undefined) {
          return invalidDelivery("ReceiptHandle", "SQS delivery did not contain a receipt handle.", "");
        }
        const receiveCount = parseReceiveCount(message.receiveCount);
        const decoded = decodePlatformQueueMessage(message.messageId, message.body);
        if (!decoded.ok) {
          return {
            kind: "invalid",
            receiptHandle: message.receiptHandle,
            receiveCount,
            error: decoded.error,
          };
        }
        return {
          kind: "delivery",
          receiptHandle: message.receiptHandle,
          receiveCount,
          message: decoded.value,
        };
      } catch {
        throw operationError("receive");
      }
    },
    acknowledge: async (receiptHandle) => {
      assertNonEmpty("receiptHandle", receiptHandle);
      try {
        await options.client.send(new DeleteMessageCommand({ QueueUrl: options.queueUrl, ReceiptHandle: receiptHandle }));
      } catch {
        throw operationError("acknowledge");
      }
    },
    release: async (receiptHandle) => {
      assertNonEmpty("receiptHandle", receiptHandle);
      try {
        await options.client.send(new ChangeMessageVisibilityCommand({
          QueueUrl: options.queueUrl,
          ReceiptHandle: receiptHandle,
          VisibilityTimeout: 0,
        }));
      } catch {
        throw operationError("release");
      }
    },
  };
}

export function createAwsSdkPlatformSqsWorkerQueue(
  options: AwsSdkPlatformSqsWorkerQueueOptions,
): PlatformSqsWorkerQueue {
  assertNonEmpty("region", options.region);
  return createPlatformSqsWorkerQueue({
    queueUrl: options.queueUrl,
    waitTimeSeconds: options.waitTimeSeconds,
    visibilityTimeoutSeconds: options.visibilityTimeoutSeconds,
    client: new SQSClient({ region: options.region }) as unknown as PlatformSqsCommandClient,
  });
}

export function createAwsSdkPlatformSqsWorkerQueueFromEnv(
  env: Readonly<Record<string, string | undefined>>,
): { readonly ok: true; readonly value: PlatformSqsWorkerQueue } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const queueUrl = requiredString(env, "PLATFORM_WORKER_SQS_QUEUE_URL");
  const region = requiredString(env, "PLATFORM_WORKER_SQS_REGION");
  const waitTimeSeconds = boundedInteger(env, "PLATFORM_WORKER_SQS_WAIT_TIME_SECONDS", 0, 20);
  const visibilityTimeoutSeconds = boundedInteger(env, "PLATFORM_WORKER_SQS_VISIBILITY_TIMEOUT_SECONDS", 0, 43_200);
  if (!queueUrl.ok) return queueUrl;
  if (!region.ok) return region;
  if (!waitTimeSeconds.ok) return waitTimeSeconds;
  if (!visibilityTimeoutSeconds.ok) return visibilityTimeoutSeconds;
  return {
    ok: true,
    value: createAwsSdkPlatformSqsWorkerQueue({
      queueUrl: queueUrl.value,
      region: region.value,
      waitTimeSeconds: waitTimeSeconds.value,
      visibilityTimeoutSeconds: visibilityTimeoutSeconds.value,
    }),
  };
}

function firstSqsMessage(response: unknown): { readonly messageId: string | undefined; readonly receiptHandle: string | undefined; readonly body: string | undefined; readonly receiveCount: string | undefined } | undefined {
  if (!isRecord(response) || !Array.isArray(response.Messages)) return undefined;
  const first = response.Messages[0];
  if (!isRecord(first)) return undefined;
  const attributes = isRecord(first.Attributes) ? first.Attributes : {};
  return {
    messageId: stringValue(first.MessageId),
    receiptHandle: stringValue(first.ReceiptHandle),
    body: stringValue(first.Body),
    receiveCount: stringValue(attributes.ApproximateReceiveCount),
  };
}

function decodePlatformQueueMessage(
  messageId: string | undefined,
  body: string | undefined,
): { readonly ok: true; readonly value: QueueMessage } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  if (messageId === undefined || messageId.length === 0) return invalidMessage("MessageId", "SQS delivery did not contain a message ID.");
  if (body === undefined || body.length === 0) return invalidMessage("Body", "SQS delivery did not contain a message body.");
  try {
    const parsed: unknown = JSON.parse(body);
    if (!isRecord(parsed)) return invalidMessage("Body", "Expected a platform queue message object.");
    const type = stringValue(parsed.type);
    const version = numberValue(parsed.version);
    const enqueuedAt = stringValue(parsed.enqueuedAt);
    if (type === undefined || version === undefined || enqueuedAt === undefined || !isQueuePayload(parsed.payload)) {
      return invalidMessage("Body", "Expected a valid platform queue message envelope.");
    }
    const queueType = queueMessageType(type);
    const queueVersion = queueMessageVersion(version);
    const queuedAt = isoDateTime(enqueuedAt);
    if (!queueType.ok || !queueVersion.ok || !queuedAt.ok) {
      return invalidMessage("Body", "Expected a valid platform queue message envelope.");
    }
    return {
      ok: true,
      value: queueMessage({
        id: queueMessageId(messageId),
        type: queueType.value,
        version: queueVersion.value,
        enqueuedAt: queuedAt.value,
        ...(optionalString(parsed.tenantId) === undefined ? {} : { tenantId: tenantId(optionalString(parsed.tenantId) as string) }),
        ...(optionalString(parsed.correlationId) === undefined ? {} : { correlationId: correlationId(optionalString(parsed.correlationId) as string) }),
        ...(optionalString(parsed.idempotencyKey) === undefined ? {} : { idempotencyKey: queueIdempotencyKey(optionalString(parsed.idempotencyKey) as string) }),
        payload: parsed.payload,
      }),
    };
  } catch {
    return invalidMessage("Body", "Expected JSON for a platform queue message envelope.");
  }
}

function requiredString(
  env: Readonly<Record<string, string | undefined>>,
  path: string,
): { readonly ok: true; readonly value: string } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const value = env[path];
  if (value === undefined || value.trim().length === 0) return invalidConfig(path, "A non-empty value is required.");
  return { ok: true, value };
}

function boundedInteger(
  env: Readonly<Record<string, string | undefined>>,
  path: string,
  min: number,
  max: number,
): { readonly ok: true; readonly value: number } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const value = Number(env[path]);
  if (!Number.isInteger(value) || value < min || value > max) return invalidConfig(path, `Expected an integer from ${min} to ${max}.`);
  return { ok: true, value };
}

function parseReceiveCount(value: string | undefined): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : 1;
}

function invalidConfig(path: string, reason: string): { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_CONFIG_INVALID", defaultMessage: "AWS SQS worker queue configuration is invalid.", details: { path, reason } } };
}

function invalidMessage(path: string, reason: string): { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  return { ok: false, error: { code: "PLATFORM_ADAPTER_AWS_SQS_MESSAGE_INVALID", defaultMessage: "SQS delivery is not a valid platform queue message.", details: { path, reason } } };
}

function invalidDelivery(path: string, reason: string, receiptHandle: string): PlatformSqsReceiveResult {
  if (receiptHandle.length === 0) {
    throw operationError("receive");
  }
  return { kind: "invalid", receiptHandle, receiveCount: 1, error: invalidMessage(path, reason).error };
}

function operationError(operation: string): PlatformSqsWorkerQueueError {
  return { code: "PLATFORM_ADAPTER_AWS_SQS_OPERATION_FAILED", defaultMessage: `AWS SQS ${operation} operation failed.` };
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined;
}

function numberValue(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isJsonValue(value: unknown): value is JsonValue {
  if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") return true;
  if (Array.isArray(value)) return value.every(isJsonValue);
  return isRecord(value) && Object.values(value).every(isJsonValue);
}

function isQueuePayload(value: unknown): value is QueuePayload {
  return isRecord(value) && Object.values(value).every(isJsonValue);
}

function assertNonEmpty(name: string, value: string): void {
  if (value.length === 0) throw new RangeError(`${name} must not be empty.`);
}

function assertWholeNumberInRange(name: string, value: number, min: number, max: number): void {
  if (!Number.isInteger(value) || value < min || value > max) {
    throw new RangeError(`${name} must be an integer from ${min} to ${max}.`);
  }
}
