import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

export const coreEventValidationDiagnostic = defineDiagnostic({ code: "core.events.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["event-type", "event-version"] },
    field: { type: "enum", values: ["type", "version"] },
    reason: { type: "enum", values: ["invalid-format", "not-integer", "not-positive"] },
    effect: { type: "enum", values: ["rejected"] },
  } },
} as const);
export const coreEventBoundaryDiagnostic = defineDiagnostic({ code: "core.events.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["event-type", "event-version", "envelope", "bus-construction", "publish", "published-events"] },
    phase: { type: "enum", values: ["predicate", "parameter-formatting", "input-projection", "payload-copy", "handler-declaration", "batch-copy", "event-iteration", "handler-iteration", "handler-selection", "handler-argument-copy", "handler-invocation", "handler-completion", "published-append", "snapshot-copy"] },
    field: { type: "enum", values: ["type", "version", "id", "occurred-at", "tenant-id", "correlation-id", "causation-id", "payload", "handlers", "events", "handler"] },
    reason: { type: "enum", values: ["threw", "rejected"] },
    effect: { type: "enum", values: ["result-not-returned", "bus-not-created", "publish-not-appended", "append-outcome-unknown", "snapshot-not-returned"] },
    handlerEffect: { type: "enum", values: ["not-invoked", "unknown"] },
    eventOrdinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    handlerOrdinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["field", "handlerEffect", "eventOrdinal", "handlerOrdinal"] },
} as const);
export const coreEventDiagnosticDefinitions = Object.freeze([coreEventValidationDiagnostic, coreEventBoundaryDiagnostic]);
export type CoreEventValidationDetail = NonNullable<typeof coreEventValidationDiagnostic.__detail>;
export type CoreEventBoundaryDetail = NonNullable<typeof coreEventBoundaryDiagnostic.__detail>;
export interface CoreEventDiagnosticContext {
  readonly operation: CoreEventValidationDetail["operation"] | CoreEventBoundaryDetail["operation"];
  readonly phase?: CoreEventBoundaryDetail["phase"];
  readonly field?: CoreEventBoundaryDetail["field"];
}
export interface CoreEventDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: CoreEventDiagnosticContext) => unknown;
}
export interface CoreEventErrorEvidence {
  readonly relatedDiagnosticRecords?: readonly DiagnosticRecord[];
  readonly relatedDiagnosticDefinitions: readonly DiagnosticDefinition[];
}
export function coreEventValidationDiagnosticRecord(detail: CoreEventValidationDetail) { return required(coreEventValidationDiagnostic, detail); }
export function coreEventBoundaryDiagnosticRecord(detail: CoreEventBoundaryDetail) { return required(coreEventBoundaryDiagnostic, detail); }
function required<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const record = createDiagnosticRecord(definition, detail);
  if (!record.ok) throw new TypeError("CORE_EVENT_DIAGNOSTIC_INVALID");
  return record.value;
}
