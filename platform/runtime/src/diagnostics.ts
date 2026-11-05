import { coreDiagnosticCatalog } from "@kanbien/core";
import { captureDiagnosticRecord, createDiagnosticRecord, defineDiagnostic, deliverDiagnosticRecord, diagnosticProcessingRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, type DiagnosticDefinition, type DiagnosticEvidence, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import type { PlatformDiagnosticCatalog, PlatformDiagnosticContext } from "@kanbien/platform-contracts";

export type PlatformRuntimeDiagnosticObserver = (
  record: DiagnosticRecord, context: PlatformDiagnosticContext,
  registeredCatalogs?: readonly PlatformDiagnosticCatalog[],
) => unknown;
export interface PlatformRuntimeDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: PlatformRuntimeDiagnosticObserver;
}
export const platformRuntimeStateDiagnostic = defineDiagnostic({
  code: "platform-runtime.state-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["start", "begin-drain", "shutdown"] },
    state: { type: "enum", values: ["created", "starting", "ready", "stopping", "stopped", "failed"] },
    effect: { type: "enum", values: ["state-unchanged"] },
  } },
});
export const platformRuntimeBoundaryDiagnostic = defineDiagnostic({
  code: "platform-runtime.boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["construct-lifecycle", "mount", "start", "shutdown", "events", "context-deps", "request-context", "job-context"] },
    phase: { type: "enum", values: ["resources-snapshot", "telemetry-snapshot", "apps-snapshot", "clock-selection",
      "app.beforeStart", "resource.start", "app.afterStart", "app.beforeStop", "resource.drain", "resource.close", "telemetry.flush", "app.afterStop",
      "events-projection", "registry-construction", "app-iteration", "app-identity", "app-uniqueness", "app-mount", "mount-error-projection", "registry-validation", "mount-projection",
      "dependency-selection", "timestamp-selection", "clock-read", "timestamp-normalization", "context-projection"] },
    subject: { type: "enum", values: ["runtime", "app", "resource", "telemetry", "context"] },
    boundary: { type: "enum", values: ["selection", "iteration", "invocation", "completion", "event-selection", "event-clock", "event-normalization", "event-append", "projection"] },
    effect: { type: "enum", values: ["step-not-invoked", "step-completion-unobserved", "step-completed-event-unrecorded", "step-completed-event-outcome-unknown", "boundary-outcome-unknown", "context-not-returned", "cleanup-completed-result-not-returned", "mount-completed-result-not-returned"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["ordinal"] },
});
export const platformRuntimeDiagnosticCatalog = Object.freeze({ owner: "platform-runtime", definitions: Object.freeze([platformRuntimeStateDiagnostic, platformRuntimeBoundaryDiagnostic]) });
export type RuntimeBoundaryDetail = NonNullable<typeof platformRuntimeBoundaryDiagnostic.__detail>;
export type RuntimeStateDetail = NonNullable<typeof platformRuntimeStateDiagnostic.__detail>;
export type RuntimeEvidence = DiagnosticEvidence;

function contextFor(operation: RuntimeBoundaryDetail["operation"] | RuntimeStateDetail["operation"]): PlatformDiagnosticContext {
  return { capability: "platform-runtime", operation,
    stage: operation === "shutdown" || operation === "begin-drain" ? "shutdown"
      : operation === "mount" || operation === "start" || operation === "construct-lifecycle" ? "startup"
        : operation === "request-context" || operation === "job-context" ? "request" : "runtime" };
}
function observe(options: PlatformRuntimeDiagnosticOptions, record: DiagnosticRecord, context: PlatformDiagnosticContext, catalogs?: readonly PlatformDiagnosticCatalog[]): void {
  deliverDiagnosticRecord(record, selected => options.onDiagnostic?.(selected, context, catalogs));
}
function selected(options: PlatformRuntimeDiagnosticOptions, cause: unknown, notices: DiagnosticRecord[], catalogs?: readonly PlatformDiagnosticCatalog[]): RuntimeEvidence {
  let definitions = [...coreDiagnosticCatalog.definitions, ...platformRuntimeDiagnosticCatalog.definitions];
  try { definitions = [...definitions, ...(options.diagnosticDefinitions ?? []), ...(catalogs ?? []).flatMap((catalog) => catalog.definitions)]; }
  catch { notices.push(diagnosticProcessingRecord("definition-selection-failed")); }
  return selectDiagnosticEvidenceWithReport(definitions, cause, record => notices.push(record));
}
export function runtimeBoundaryEvidence(options: PlatformRuntimeDiagnosticOptions, detail: RuntimeBoundaryDetail, cause: unknown,
  catalogs?: readonly PlatformDiagnosticCatalog[], includeUpstream = true): RuntimeEvidence {
  const own = requireDiagnosticRecord([platformRuntimeBoundaryDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(platformRuntimeBoundaryDiagnostic, detail);
    return checked.ok ? checked.value : undefined;
  }));
  const notices: DiagnosticRecord[] = [];
  const retained = includeUpstream ? selected(options, cause, notices, catalogs) : {};
  const context = contextFor(detail.operation);
  observe(options, own, context, catalogs);
  if (retained.diagnosticRecord !== undefined) observe(options, retained.diagnosticRecord, context, catalogs);
  const companions = retained.relatedDiagnosticRecords;
  if (companions !== undefined) for (let index = 0; index < companions.length; index++) observe(options, companions[index]!, context, catalogs);
  for (const notice of notices) observe(options, notice, context, catalogs);
  return { diagnosticRecord: retained.diagnosticRecord ?? own,
    ...(retained.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: retained.relatedDiagnosticRecords }) };
}
export function runtimeStateEvidence(options: PlatformRuntimeDiagnosticOptions, detail: RuntimeStateDetail): RuntimeEvidence {
  const own = requireDiagnosticRecord([platformRuntimeStateDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(platformRuntimeStateDiagnostic, detail);
    return checked.ok ? checked.value : undefined;
  }));
  observe(options, own, contextFor(detail.operation));
  return { diagnosticRecord: own };
}
