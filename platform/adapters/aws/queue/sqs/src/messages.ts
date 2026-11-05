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
  type CoreQueueDiagnosticOptions,
  type CoreQueueBoundaryDetail,
  type DiagnosticRecord,
  selectCoreQueueDiagnosticEvidence,
} from "@kanbien/core";
import { invalidMessage, type PlatformSqsWorkerQueueError } from "./errors";
import { sqsObservation, type SqsObservation } from "./observations";

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
  options?: CoreQueueDiagnosticOptions,
): { readonly ok: true; readonly value: QueueMessage } | { readonly ok: false; readonly error: PlatformSqsWorkerQueueError } {
  const observed = sqsObservation(options, "decode");
  if (observed.at("selection", () => body === undefined || body.length === 0)) return invalidMessage("Body", "SQS delivery did not contain a message body.", observed.reject("body", body === undefined ? "missing" : "empty"));
  let boundary: CoreQueueBoundaryDetail["boundary"] = "json-parse";
  try {
    const parsed: unknown = JSON.parse(body!);
    boundary = "envelope";
    if (!isRecord(parsed)) return invalidMessage("Body", "Expected a platform queue message object.", observed.reject("envelope", "not-record"));
    const rawId = parsed.id;
    const id = optionalString(rawId);
    const rawType = parsed.type;
    const type = optionalString(rawType);
    const rawVersion = parsed.version;
    const version = numberValue(rawVersion);
    const rawEnqueuedAt = parsed.enqueuedAt;
    const enqueuedAt = optionalString(rawEnqueuedAt);
    boundary = "trace-parent";
    const traceParent = parsed.traceParent === undefined ? { ok: true as const, value: undefined } : parseTraceParent(parsed.traceParent, observed);
    boundary = "envelope";
    let field: "id" | "message-type" | "message-version" | "enqueued-at" | "payload" | "trace-parent" = "id";
    if (id === undefined || (field = "message-type", type === undefined) || (field = "message-version", version === undefined) || (field = "enqueued-at", enqueuedAt === undefined) || (field = "payload", !isQueuePayload(parsed.payload)) || (field = "trace-parent", !traceParent.ok)) {
      if (field !== "trace-parent") {
        const raw = field === "id" ? rawId : field === "message-type" ? rawType : field === "message-version" ? rawVersion : rawEnqueuedAt;
        observed.reject(field, field === "payload" ? "predicate-rejected" : raw === undefined ? "missing" : field === "message-version" ? typeof raw === "number" ? "not-finite" : "wrong-type" : typeof raw === "string" ? "empty" : "wrong-type");
      }
      return invalidMessage("Body", "Expected a valid platform queue message envelope.", observed.evidence());
    }
    const queueType = queueMessageType(type);
    const queueVersion = queueMessageVersion(version);
    const queuedAt = isoDateTime(enqueuedAt);
    if (!queueType.ok || !queueVersion.ok || !queuedAt.ok) {
      const sources: DiagnosticRecord[] = [];
      for (const result of [queueType, queueVersion, queuedAt]) {
        const error = Object.getOwnPropertyDescriptor(result, "error");
        const source = selectCoreQueueDiagnosticEvidence(options, error !== undefined && "value" in error ? error.value : undefined);
        if (source.diagnosticRecord !== undefined) sources.push(source.diagnosticRecord);
        sources.push(...(source.relatedDiagnosticRecords ?? []));
      }
      observed.reject("envelope", "predicate-rejected", { diagnosticRecord: sources[0], relatedDiagnosticRecords: sources.slice(1) });
      return invalidMessage("Body", "Expected a valid platform queue message envelope.", observed.evidence());
    }
    boundary = "payload-copy";
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
  } catch (cause) {
    observed.failure(boundary, cause);
    return invalidMessage("Body", "Expected JSON for a platform queue message envelope.", observed.evidence());
  }
}

function parseTraceParent(
  value: unknown,
  observed: SqsObservation,
): { readonly ok: true; readonly value: ReturnType<typeof traceContext> } | { readonly ok: false } {
  if (!isRecord(value)) { observed.reject("trace-parent", "not-record"); return { ok: false }; }
  const rawTraceId = value.traceId;
  const receivedTraceId = optionalString(rawTraceId);
  const rawSpanId = value.spanId;
  const receivedSpanId = optionalString(rawSpanId);
  const receivedParentSpanId = optionalString(value.parentSpanId);
  if (receivedTraceId === undefined || receivedSpanId === undefined) {
    const raw = receivedTraceId === undefined ? rawTraceId : rawSpanId;
    observed.reject(receivedTraceId === undefined ? "trace-id" : "span-id", raw === undefined ? "missing" : typeof raw === "string" ? "empty" : "wrong-type"); return { ok: false };
  }
  try {
    return {
      ok: true,
      value: traceContext({
        traceId: traceId(receivedTraceId),
        spanId: spanId(receivedSpanId),
        ...(receivedParentSpanId === undefined ? {} : { parentSpanId: spanId(receivedParentSpanId) }),
      }),
    };
  } catch (cause) {
    observed.failure("trace-parent", cause);
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
