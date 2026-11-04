import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreMonitoringBoundaryDiagnosticRecord, coreMonitoringValidationDiagnosticRecord, type CoreMonitoringBoundaryDetail, type CoreMonitoringDiagnosticContext, type CoreMonitoringDiagnosticOptions, type CoreMonitoringValidationDetail } from "./boundary-diagnostics";

export function selectCoreMonitoringDiagnosticEvidence(options: CoreMonitoringDiagnosticOptions | undefined, cause: unknown) {
  let definitions: readonly DiagnosticDefinition[] = coreDiagnosticCatalog.definitions;
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Optional selection is unavailable. */ }
  return selectDiagnosticEvidence(definitions, cause);
}
const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional observer. */ } }
}
export function observeCoreMonitoringDiagnostic(options: CoreMonitoringDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown) {
  const selected = selectCoreMonitoringDiagnosticEvidence(options, cause);
  const checked = selectCoreMonitoringDiagnosticEvidence(options, { diagnosticRecord: own }).diagnosticRecord;
  if (checked === undefined || !["core.monitoring.validation-rejected", "core.monitoring.boundary-failed"].includes(checked.code)) return selected;
  const detail = checked.detail as CoreMonitoringDiagnosticContext;
  const context = Object.freeze({ operation: detail.operation, ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { try { isolate(options?.onDiagnostic?.(record, context)); } catch { /* Preserve receiver and workload. */ } };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
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
    const record = coreMonitoringValidationDiagnosticRecord({ operation: this.operation as CoreMonitoringValidationDetail["operation"], field, reason, effect: "rejected", ...(ordinal === undefined ? {} : { ordinal }) });
    const error = Object.assign(new TypeError(message), { diagnosticRecord: record });
    this.rejection = error;
    observeCoreMonitoringDiagnostic(this.options, record);
    return error;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      if (cause !== this.rejection) observeCoreMonitoringDiagnostic(this.options, coreMonitoringBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason: "threw", effect: this.effect }), cause);
      throw cause;
    }
  }
}
