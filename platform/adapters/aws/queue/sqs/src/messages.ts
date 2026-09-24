import {
  causationId,
  correlationId,
  isoDateTime,
  queueIdempotencyKey,
  queueMessage,
  queueMessageGroupKey,
  queueMessageId,
  queueMessageType,
  queueMessageVersion,
  spanId,
  tenantId,
  traceContext,
  traceId,
  type JsonValue,
  type QueueMessage,
  type QueuePayload,
} from "@kanbien/core";
import { invalidMessage, type PlatformSqsWorkerQueueError } from "./errors";

/**
 * Encode the complete Core envelope so a provider delivery ID can never become
 * the durable identity that an outbox worker uses for idempotency.
 */
export function encodePlatformQueueMessage(message: QueueMessage): string {
  return JSON.stringify({
    id: String(message.id),
    type: String(message.type),
    version: Number(message.version),
    enqueuedAt: String(message.enqueuedAt),
    ...(message.tenantId === undefined ? {} : { tenantId: String(message.tenantId) }),
    ...(message.correlationId === undefined ? {} : { correlationId: String(message.correlationId) }),
    ...(message.causationId === undefined ? {} : { causationId: String(message.causationId) }),
    ...(message.traceParent === undefined
      ? {}
      : {
          traceParent: {
            traceId: String(message.traceParent.traceId),
            spanId: String(message.traceParent.spanId),
            ...(message.traceParent.parentSpanId === undefined ? {} : { parentSpanId: String(message.traceParent.parentSpanId) }),
          },
        }),
    ...(message.idempotencyKey === undefined ? {} : { idempotencyKey: String(message.idempotencyKey) }),
    ...(message.messageGroupKey === undefined ? {} : { messageGroupKey: String(message.messageGroupKey) }),
    payload: message.payload,
  });
}

export function decodePlatformQueueMessage(
  body: string | undefined,
): { readonly ok: true; readonly value: QueueMessage } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  if (body === undefined || body.length === 0) return invalidMessage("Body", "SQS delivery did not contain a message body.");
  try {
    const parsed: unknown = JSON.parse(body);
    if (!isRecord(parsed)) return invalidMessage("Body", "Expected a platform queue message object.");
    const id = optionalString(parsed.id);
    const type = optionalString(parsed.type);
    const version = numberValue(parsed.version);
    const enqueuedAt = optionalString(parsed.enqueuedAt);
    const traceParent = parsed.traceParent === undefined ? { ok: true as const, value: undefined } : parseTraceParent(parsed.traceParent);
    if (id === undefined || type === undefined || version === undefined || enqueuedAt === undefined || !isQueuePayload(parsed.payload) || !traceParent.ok) {
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
        id: queueMessageId(id),
        type: queueType.value,
        version: queueVersion.value,
        enqueuedAt: queuedAt.value,
        ...(optionalString(parsed.tenantId) === undefined ? {} : { tenantId: tenantId(optionalString(parsed.tenantId) as string) }),
        ...(optionalString(parsed.correlationId) === undefined ? {} : { correlationId: correlationId(optionalString(parsed.correlationId) as string) }),
        ...(optionalString(parsed.causationId) === undefined ? {} : { causationId: causationId(optionalString(parsed.causationId) as string) }),
        ...(traceParent.value === undefined ? {} : { traceParent: traceParent.value }),
        ...(optionalString(parsed.idempotencyKey) === undefined ? {} : { idempotencyKey: queueIdempotencyKey(optionalString(parsed.idempotencyKey) as string) }),
        ...(optionalString(parsed.messageGroupKey) === undefined ? {} : { messageGroupKey: queueMessageGroupKey(optionalString(parsed.messageGroupKey) as string) }),
        payload: parsed.payload,
      }),
    };
  } catch {
    return invalidMessage("Body", "Expected JSON for a platform queue message envelope.");
  }
}

function parseTraceParent(
  value: unknown,
): { readonly ok: true; readonly value: ReturnType<typeof traceContext> } | { readonly ok: false } {
  if (!isRecord(value)) return { ok: false };
  const receivedTraceId = optionalString(value.traceId);
  const receivedSpanId = optionalString(value.spanId);
  const receivedParentSpanId = optionalString(value.parentSpanId);
  if (receivedTraceId === undefined || receivedSpanId === undefined) return { ok: false };
  try {
    return {
      ok: true,
      value: traceContext({
        traceId: traceId(receivedTraceId),
        spanId: spanId(receivedSpanId),
        ...(receivedParentSpanId === undefined ? {} : { parentSpanId: spanId(receivedParentSpanId) }),
      }),
    };
  } catch {
    return { ok: false };
  }
}

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
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
