import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

export const coreQueueValidationDiagnostic = defineDiagnostic({ code: "core.queue.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["validate", "send", "receive", "decode", "acknowledge", "release"] },
    field: { type: "enum", values: ["message-type", "message-version", "delay", "attempt", "dead-letter-reason", "idempotency-key", "message-group-key", "retry-attempt", "delivery-disposition", "body", "envelope", "id", "enqueued-at", "payload", "trace-parent", "trace-id", "span-id", "parent-span-id", "receipt-handle"] },
    reason: { type: "enum", values: ["missing", "empty", "wrong-type", "not-record", "not-finite", "not-integer", "not-positive", "negative", "above-maximum", "invalid-format", "unsupported", "exceeds-maximum-attempt", "conflicting", "predicate-rejected"] },
    effect: { type: "enum", values: ["rejected"] },
  } },
} as const);
export const coreQueueBoundaryDiagnostic = defineDiagnostic({ code: "core.queue.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["client-initialization", "send", "receive", "decode", "acknowledge", "release"] },
    boundary: { type: "enum", values: ["construction", "selection", "encoding", "invocation", "response", "json-parse", "envelope", "trace-parent", "payload-copy"] },
    reason: { type: "enum", values: ["threw", "rejected", "returned-failure"] },
    effect: { type: "enum", values: ["not-invoked", "unknown", "not-assessed"] },
    native: { type: "object", properties: {
      codeAvailability: { type: "enum", values: ["absent", "wrong-type", "unavailable", "recognized", "unrecognized"] },
      condition: { type: "enum", values: ["queue-absent-reported", "receipt-rejected", "message-not-in-flight", "address-rejected", "message-content-rejected", "request-security-rejected", "operation-unsupported", "request-throttled", "limit-reported", "key-access-rejected", "key-throttled", "key-rejected", "unknown"] },
    } },
  }, optional: ["native"] },
} as const);
export const coreQueueReceiveReductionDiagnostic = defineDiagnostic({ code: "core.queue.receive-reduced", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["receive"] },
    issues: { type: "array", minItems: 1, maxItems: 16, items: { type: "object", properties: {
      field: { type: "enum", values: ["response", "messages", "message", "attributes", "receipt-handle", "body", "receive-count"] },
      reason: { type: "enum", values: ["absent", "empty", "not-record", "not-array", "wrong-type", "not-integer", "not-positive"] },
      reduction: { type: "enum", values: ["empty-receive", "empty-attributes", "field-unavailable", "count-one"] },
      count: { type: "integer", minimum: 1, maximum: Number.MAX_SAFE_INTEGER },
    }, optional: ["count"] } },
    truncated: { type: "boolean" },
    effect: { type: "enum", values: ["reduction-observed"] },
  } },
} as const);
export const coreQueueDiagnosticDefinitions = Object.freeze([coreQueueValidationDiagnostic, coreQueueBoundaryDiagnostic, coreQueueReceiveReductionDiagnostic]);
export type CoreQueueValidationDetail = NonNullable<typeof coreQueueValidationDiagnostic.__detail>;
export type CoreQueueBoundaryDetail = NonNullable<typeof coreQueueBoundaryDiagnostic.__detail>;
export type CoreQueueReceiveReductionDetail = NonNullable<typeof coreQueueReceiveReductionDiagnostic.__detail>;
export interface CoreQueueDiagnosticContext {
  readonly operation: CoreQueueValidationDetail["operation"] | CoreQueueBoundaryDetail["operation"] | CoreQueueReceiveReductionDetail["operation"];
  readonly boundary?: CoreQueueBoundaryDetail["boundary"];
}
export interface CoreQueueDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreQueueDiagnosticContext) => unknown;
}
function requiredRecord<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const result = createDiagnosticRecord(definition, detail);
  if (!result.ok) throw new TypeError("CORE_QUEUE_DIAGNOSTIC_INVALID");
  return result.value;
}
export function coreQueueValidationDiagnosticRecord(detail: CoreQueueValidationDetail) { return requiredRecord(coreQueueValidationDiagnostic, detail); }
export function coreQueueBoundaryDiagnosticRecord(detail: CoreQueueBoundaryDetail) { return requiredRecord(coreQueueBoundaryDiagnostic, detail); }
export function coreQueueReceiveReductionDiagnosticRecord(detail: CoreQueueReceiveReductionDetail) { return requiredRecord(coreQueueReceiveReductionDiagnostic, detail); }
