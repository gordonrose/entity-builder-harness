import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreMonitoringDiagnosticDefinitions, coreMonitoringBoundaryDiagnosticRecord, coreMonitoringValidationDiagnosticRecord, type CoreMonitoringBoundaryDetail, type CoreMonitoringDiagnosticContext, type CoreMonitoringDiagnosticOptions, type CoreMonitoringValidationDetail } from "./boundary-diagnostics";

export function selectCoreMonitoringDiagnosticEvidence(options: CoreMonitoringDiagnosticOptions | undefined, cause: unknown, onProcessing?: (record: DiagnosticRecord) => unknown) {
  let definitions: readonly DiagnosticDefinition[] = coreDiagnosticCatalog.definitions;
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; }
  catch { deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record)); }
  return onProcessing === undefined ? selectDiagnosticEvidence(definitions, cause) : selectDiagnosticEvidenceWithReport(definitions, cause, onProcessing);
}
export function observeCoreMonitoringDiagnostic(options: CoreMonitoringDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown, fallback?: CoreMonitoringDiagnosticContext) {
  const processing: DiagnosticRecord[] = [];
  const selected = selectCoreMonitoringDiagnosticEvidence(options, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(coreMonitoringDiagnosticDefinitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreMonitoringDiagnosticContext;
  if (detail === undefined) return { ...selected, diagnosticRecord: selected.diagnosticRecord ?? checked };
  const context = Object.freeze({ operation: detail.operation, ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, context)); };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  for (const record of processing) deliver(record);
  return selected;
}

/** Per-invocation provenance; an old guard error thrown by a getter is not a new rejection. */
export class MonitoringObservation {
  private phase: CoreMonitoringBoundaryDetail["phase"] = "input-projection";
  private field: CoreMonitoringBoundaryDetail["field"] | undefined;
  private effect: CoreMonitoringBoundaryDetail["effect"] = "result-not-returned";
  private rejection: unknown = {};
  constructor(private readonly operation: CoreMonitoringBoundaryDetail["operation"], private readonly options: CoreMonitoringDiagnosticOptions | undefined) {}
  at<T>(phase: CoreMonitoringBoundaryDetail["phase"], field: CoreMonitoringBoundaryDetail["field"] | undefined, action: () => T): T {
    this.phase = phase; this.field = field; return action();
  }
  effectIs(effect: CoreMonitoringBoundaryDetail["effect"]): void { this.effect = effect; }
  existingRejection(error: TypeError): TypeError { this.rejection = error; return error; }
  reject(message: string, field: CoreMonitoringValidationDetail["field"], reason: CoreMonitoringValidationDetail["reason"], ordinal?: number): TypeError {
    const record = requireDiagnosticRecord(coreMonitoringDiagnosticDefinitions, captureDiagnosticRecord(() => coreMonitoringValidationDiagnosticRecord({ operation: this.operation as CoreMonitoringValidationDetail["operation"], field, reason, effect: "rejected", ...(ordinal === undefined ? {} : { ordinal }) })));
    const error = Object.assign(new TypeError(message), { diagnosticRecord: record });
    this.rejection = error;
    observeCoreMonitoringDiagnostic(this.options, record, undefined, { operation: this.operation, field });
    return error;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      if (cause !== this.rejection) {
        const detail: CoreMonitoringBoundaryDetail = { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason: "threw", effect: this.effect };
        observeCoreMonitoringDiagnostic(this.options, captureDiagnosticRecord(() => coreMonitoringBoundaryDiagnosticRecord(detail)), cause, detail);
      }
      throw cause;
    }
  }
}
