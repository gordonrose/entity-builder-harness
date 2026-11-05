import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreLoggingDiagnosticDefinitions, coreLoggingBoundaryDiagnosticRecord, type CoreLoggingBoundaryDetail, type CoreLoggingDiagnosticContext, type CoreLoggingDiagnosticOptions } from "./diagnostics";
export function selectCoreLoggingDiagnosticEvidence(options: CoreLoggingDiagnosticOptions | undefined, cause: unknown, onProcessing?: (record: DiagnosticRecord) => unknown) {
  let definitions: readonly DiagnosticDefinition[] = coreDiagnosticCatalog.definitions;
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; }
  catch { deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record)); }
  return onProcessing === undefined ? selectDiagnosticEvidence(definitions, cause) : selectDiagnosticEvidenceWithReport(definitions, cause, onProcessing);
}
const nativeThen = Promise.prototype.then;
export function observeCoreLoggingDiagnostic(options: CoreLoggingDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown, fallback?: CoreLoggingDiagnosticContext) {
  const processing: DiagnosticRecord[] = [];
  const selected = selectCoreLoggingDiagnosticEvidence(options, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(coreLoggingDiagnosticDefinitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreLoggingDiagnosticContext;
  if (detail === undefined) return { ...selected, diagnosticRecord: selected.diagnosticRecord ?? checked };
  const context = Object.freeze({ operation: detail.operation, phase: detail.phase, ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, context)); };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  for (const record of processing) deliver(record);
  return selected;
}
export class LoggingObservation {
  private phase: CoreLoggingBoundaryDetail["phase"] = "input-projection";
  private field: CoreLoggingBoundaryDetail["field"] | undefined;
  private effect: CoreLoggingBoundaryDetail["effect"] = "result-not-returned";
  constructor(private readonly operation: CoreLoggingBoundaryDetail["operation"], private readonly options: CoreLoggingDiagnosticOptions | undefined) {}
  at<T>(phase: CoreLoggingBoundaryDetail["phase"], field: CoreLoggingBoundaryDetail["field"] | undefined, action: () => T): T { this.phase = phase; this.field = field; return action(); }
  effectIs(effect: CoreLoggingBoundaryDetail["effect"]): void { this.effect = effect; }
  failed(cause: unknown, reason: CoreLoggingBoundaryDetail["reason"]): void {
    const detail: CoreLoggingBoundaryDetail = { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason, effect: this.effect };
    observeCoreLoggingDiagnostic(this.options, captureDiagnosticRecord(() => coreLoggingBoundaryDiagnosticRecord(detail)), cause, detail);
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.failed(cause, "threw"); throw cause; } }
  returned(value: unknown): void {
    if (value === undefined) return;
    const rejected = (cause: unknown): void => this.failed(cause, "rejected");
    try { Reflect.apply(nativeThen, value, [undefined, rejected]); }
    catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, rejected]); } catch { /* Observation cannot change write's void outcome. */ } }
  }
}
