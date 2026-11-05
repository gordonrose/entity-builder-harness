import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { attachCoreDiagnosticRecord } from "../shared/diagnostics";
import { coreAuditDiagnosticDefinitions, coreAuditBoundaryDiagnosticRecord, coreAuditValidationDiagnosticRecord,
  type CoreAuditBoundaryDetail, type CoreAuditDiagnosticContext, type CoreAuditDiagnosticOptions, type CoreAuditValidationDetail } from "./diagnostics";

function observe(options: CoreAuditDiagnosticOptions | undefined, own: DiagnosticRecord, fallback: CoreAuditDiagnosticContext, cause?: unknown) {
  const processing: DiagnosticRecord[] = [];
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreAuditDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { processing.push(diagnosticProcessingRecord("definition-selection-failed")); }
  const selected = selectDiagnosticEvidenceWithReport(definitions, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(definitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreAuditDiagnosticContext;
  const context = Object.freeze({ operation: detail.operation,
    ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => {
    deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, context));
  };
  if (checked !== undefined) deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  for (const record of processing) deliver(record);
  if (checked !== undefined) attachCoreDiagnosticRecord(cause, checked);
  return { ...(selected.diagnosticRecord === undefined ? checked === undefined ? {} : { diagnosticRecord: checked } : { diagnosticRecord: selected.diagnosticRecord }),
    ...(selected.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: selected.relatedDiagnosticRecords }) };
}
export class AuditObservation {
  private phase: CoreAuditBoundaryDetail["phase"] = "input-projection";
  private field: CoreAuditBoundaryDetail["field"] | undefined;
  private effect: CoreAuditBoundaryDetail["effect"] = "result-not-returned";
  private ordinal: number | undefined;
  constructor(private readonly operation: CoreAuditBoundaryDetail["operation"], private readonly options: CoreAuditDiagnosticOptions | undefined) {}
  location(phase: CoreAuditBoundaryDetail["phase"], field?: CoreAuditBoundaryDetail["field"]): void { this.phase = phase; this.field = field; }
  effectIs(effect: CoreAuditBoundaryDetail["effect"]): void { this.effect = effect; }
  duringItem<T>(ordinal: number, action: () => T): T {
    const previous = this.ordinal;
    this.ordinal = ordinal;
    const value = action();
    this.ordinal = previous;
    return value;
  }
  at<T>(phase: CoreAuditBoundaryDetail["phase"], field: CoreAuditBoundaryDetail["field"] | undefined, action: () => T): T {
    const previousPhase = this.phase, previousField = this.field;
    this.location(phase, field);
    const value = action();
    this.location(previousPhase, previousField);
    return value;
  }
  validation(detail: Omit<CoreAuditValidationDetail, "effect">): DiagnosticRecord {
    const own = captureDiagnosticRecord(() => coreAuditValidationDiagnosticRecord({ ...detail, effect: "rejected" }));
    return observe(this.options, own, { operation: detail.operation, field: detail.field }).diagnosticRecord!;
  }
  failed(cause: unknown) {
    const own = captureDiagnosticRecord(() => coreAuditBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, reason: "threw", effect: this.effect,
      ...(this.field === undefined ? {} : { field: this.field }), ...(this.ordinal === undefined ? {} : { ordinal: this.ordinal }) }));
    return observe(this.options, own, { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }) }, cause);
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.failed(cause); throw cause; } }
}
