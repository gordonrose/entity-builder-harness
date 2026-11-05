import { coreDiagnosticCatalog } from "@kanbien/core";
import { captureDiagnosticRecord, requireDiagnosticRecord, diagnosticProcessingRecord, deliverDiagnosticRecord, deliverDiagnosticRecords, selectDiagnosticEvidenceWithReport, createDiagnosticRecord, defineDiagnostic, type DiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformDiagnosticContext, PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { reportPlatformDiagnostic } from "@kanbien/platform-observability";
import { platformWorkerConfigurationDiagnostic } from "./configuration-diagnostics";
import { workerRetryConfigurationDiagnosticCatalog } from "./configuration/index";

export const workerDiagnosticErrorCodes = ["PLATFORM_WORKER_MOUNT_FAILED", "PLATFORM_WORKER_CONFIG_INVALID", "PLATFORM_WORKER_QUEUE_CLOSED", "PLATFORM_WORKER_NOT_READY", "PLATFORM_WORKER_JOB_NOT_FOUND", "PLATFORM_WORKER_INVALID_PAYLOAD", "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID", "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY", "PLATFORM_WORKER_DURABLE_PROCESSING_TERMINAL_FAILURE", "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED", "PLATFORM_WORKER_HANDLER_FAILED", "PLATFORM_WORKER_IDEMPOTENCY_FAILED"] as const;

export const platformWorkerDiagnostic = defineDiagnostic({ code: "platform-worker.delivery-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    errorCode: { type: "enum", values: workerDiagnosticErrorCodes },
    phase: { type: "enum", values: ["configuration", "mount", "admission", "payload-validation", "claim", "handler", "settlement", "shutdown"] },
    reason: { type: "enum", values: ["invalid", "rejected", "attempts-exhausted", "interrupted", "unclassified"] },
    effect: { type: "enum", values: ["not-started", "rejected", "unknown"] },
  } },
} as const);
export const platformWorkerBoundaryDiagnostic = defineDiagnostic({ code: "platform-worker.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["shutdown", "process-start", "signal-shutdown", "job-delivery"] },
    phase: { type: "enum", values: ["queue-close", "startup-log", "shutdown-log", "signal-registration", "context-input", "delivery-clock"] },
    boundary: { type: "enum", values: ["selection", "invocation", "selection-or-invocation"] },
    effect: { type: "enum", values: ["lifecycle-shutdown-not-invoked", "process-not-returned", "shutdown-not-completed", "handler-not-invoked"] },
  } },
} as const);
export const platformWorkerDeliveryRejectedDiagnostic = defineDiagnostic({ code: "platform-worker.delivery-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["job-delivery", "queue-enqueue", "queue-retry"] },
    field: { type: "enum", values: ["lifecycle", "job", "payload", "outbox-id", "message-id", "idempotency-key", "completion-outcome", "claimed-lease", "queue-state"] },
    condition: { type: "enum", values: ["not-ready", "unmatched", "validator-rejected", "null", "array", "nonobject", "absent", "wrong-type", "empty", "mismatch", "closed"] },
    effect: { type: "enum", values: ["handler-not-invoked", "queue-not-mutated"] },
  } },
} as const);
export const platformWorkerCoordinationDiagnostic = defineDiagnostic({ code: "platform-worker.coordination-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    condition: { type: "enum", values: ["lease-active", "already-completed", "already-terminal", "idempotency-duplicate"] },
    effect: { type: "enum", values: ["handler-not-invoked"] },
  } },
} as const);
export const platformWorkerDeliveryBoundaryDiagnostic = defineDiagnostic({ code: "platform-worker.boundary-failed", version: 2,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["job-delivery", "queue-enqueue", "queue-retry", "queue-dead-letter"] },
    phase: { type: "enum", values: ["dequeue", "selection", "validation", "identity", "claim-clock", "claim", "claim-result", "lookup", "context", "handler", "complete-clock", "complete", "idempotency-record", "settlement-clock", "settlement", "release", "terminal-complete", "backoff", "retry", "dead-letter", "observation", "queue-clock", "queue-mutation"] },
    reason: { type: "enum", values: ["thrown", "returned-failure"] },
    effect: { type: "enum", values: ["handler-not-invoked", "handler-outcome-unknown", "handler-succeeded", "handler-failed", "settlement-unknown", "queue-not-mutated", "queue-mutation-unknown", "not-assessed"] },
  } },
} as const);
export type WorkerDeliveryBoundaryDetail = NonNullable<typeof platformWorkerDeliveryBoundaryDiagnostic.__detail>;
export function workerDeliveryRejectedRecord(detail: Omit<NonNullable<typeof platformWorkerDeliveryRejectedDiagnostic.__detail>, "operation"> & {
  readonly operation?: NonNullable<typeof platformWorkerDeliveryRejectedDiagnostic.__detail>["operation"];
}): DiagnosticRecord {
  return requiredRecord(platformWorkerDeliveryRejectedDiagnostic, { ...detail, operation: detail.operation ?? "job-delivery" });
}
export function workerCoordinationRecord(condition: NonNullable<typeof platformWorkerCoordinationDiagnostic.__detail>["condition"]): DiagnosticRecord {
  return requiredRecord(platformWorkerCoordinationDiagnostic, { condition, effect: "handler-not-invoked" });
}
export function workerDeliveryBoundaryRecord(detail: WorkerDeliveryBoundaryDetail): DiagnosticRecord {
  return requiredRecord(platformWorkerDeliveryBoundaryDiagnostic, detail);
}
function requiredRecord(definition: DiagnosticDefinition, detail: unknown): DiagnosticRecord {
  const checked = createDiagnosticRecord(definition, detail);
  if (!checked.ok) throw new TypeError("PLATFORM_WORKER_DIAGNOSTIC_INVALID");
  return checked.value;
}
export const platformWorkerDiagnosticCatalog = { owner: "platform-worker", definitions: [...workerRetryConfigurationDiagnosticCatalog.definitions, platformWorkerDiagnostic, platformWorkerConfigurationDiagnostic, platformWorkerBoundaryDiagnostic,
  platformWorkerDeliveryRejectedDiagnostic, platformWorkerCoordinationDiagnostic, platformWorkerDeliveryBoundaryDiagnostic] } as const;

/** Optional local-queue observation, independent of any Worker job's profile. */
export interface PlatformWorkerQueueDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord) => unknown;
}
export function captureWorkerDiagnostic(build: () => DiagnosticRecord | undefined): DiagnosticRecord {
  return requireDiagnosticRecord([...coreDiagnosticCatalog.definitions, ...platformWorkerDiagnosticCatalog.definitions], captureDiagnosticRecord(build));
}
export function observeWorkerQueueDiagnostic(options: PlatformWorkerQueueDiagnosticOptions, own: DiagnosticRecord, cause?: unknown): void {
  const notices: DiagnosticRecord[] = [];
  let definitions: readonly DiagnosticDefinition[] = [];
  try { definitions = options.diagnosticDefinitions ?? []; }
  catch { notices.push(diagnosticProcessingRecord("definition-selection-failed")); }
  const evidence = workerDiagnosticEvidence(cause, definitions, record => notices.push(record));
  deliverDiagnosticRecords([captureWorkerDiagnostic(() => own), ...(evidence.diagnosticRecord === undefined ? [] : [evidence.diagnosticRecord]),
    ...(evidence.relatedDiagnosticRecords ?? []), ...notices], record => options.onDiagnostic?.(record));
}

export function workerDiagnosticEvidence(cause: unknown, definitions: readonly DiagnosticDefinition[] = [], onProcessing?: (record: DiagnosticRecord) => unknown): DiagnosticEvidence {
  let selected: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformWorkerDiagnosticCatalog.definitions];
  try { selected = [...selected, ...definitions]; }
  catch { deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record)); }
  return selectDiagnosticEvidenceWithReport(selected, cause, record => onProcessing?.(record));
}

/** Raw-throw boundaries deliver their location independently; they do not decorate or replace the thrown value. */
export function reportWorkerBoundary(reporter: PlatformDiagnosticReporter, detail: NonNullable<typeof platformWorkerBoundaryDiagnostic.__detail>,
  cause: unknown, definitions: readonly DiagnosticDefinition[] = []): void {
  try {
    const context: PlatformDiagnosticContext = { capability: "platform-worker", operation: detail.operation,
      stage: detail.operation === "process-start" ? "startup" : detail.operation === "job-delivery" ? "request" : "shutdown" };
    const own = captureWorkerDiagnostic(() => {
      const checked = createDiagnosticRecord(platformWorkerBoundaryDiagnostic, detail);
      return checked.ok ? checked.value : undefined;
    });
    reportPlatformDiagnostic(reporter, own, context);
    const notices: DiagnosticRecord[] = [];
    const retained = workerDiagnosticEvidence(cause, definitions, record => notices.push(record));
    if (retained.diagnosticRecord !== undefined) reportPlatformDiagnostic(reporter, retained.diagnosticRecord, context);
    const companions = retained.relatedDiagnosticRecords;
    if (companions !== undefined) for (let index = 0; index < companions.length; index++) reportPlatformDiagnostic(reporter, companions[index]!, context);
    for (const record of notices) reportPlatformDiagnostic(reporter, record, context);
  } catch { /* Optional diagnostics cannot change source throw identity or cleanup. */ }
}

export function workerDiagnosticRecord(code: (typeof workerDiagnosticErrorCodes)[number], observedPhase?: "configuration" | "claim" | "complete" | "release") {
  const phase = observedPhase === "complete" || observedPhase === "release" ? "settlement" : observedPhase === "configuration" ? "configuration"
    : code === "PLATFORM_WORKER_MOUNT_FAILED" ? "mount" : code === "PLATFORM_WORKER_CONFIG_INVALID" ? "configuration"
    : code === "PLATFORM_WORKER_INVALID_PAYLOAD" || code === "PLATFORM_WORKER_DURABLE_OUTBOX_ENVELOPE_INVALID" ? "payload-validation"
    : code === "PLATFORM_WORKER_HANDLER_FAILED" || code === "PLATFORM_WORKER_IDEMPOTENCY_FAILED" ? "handler"
    : ["PLATFORM_WORKER_QUEUE_CLOSED", "PLATFORM_WORKER_NOT_READY", "PLATFORM_WORKER_JOB_NOT_FOUND"].includes(code) ? "admission" : "claim";
  const uncertain = phase === "handler" || code === "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED";
  const record = createDiagnosticRecord(platformWorkerDiagnostic, { errorCode: code, phase,
    reason: uncertain ? "unclassified" : phase === "configuration" || phase === "payload-validation" ? "invalid" : "rejected",
    effect: uncertain ? "unknown" : phase === "configuration" || phase === "mount" ? "not-started" : "rejected" });
  if (!record.ok) throw new TypeError("PLATFORM_WORKER_DIAGNOSTIC_INVALID");
  return record.value;
}
