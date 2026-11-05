import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreLocalizationDiagnosticDefinitions, coreLocalizationBoundaryDiagnosticRecord, coreLocalizationValidationDiagnosticRecord, coreLocalizationUnsupportedDiagnosticRecord, type CoreLocalizationBoundaryDetail, type CoreLocalizationDiagnosticContext, type CoreLocalizationDiagnosticOptions, type CoreLocalizationValidationDetail } from "./diagnostics";

export function selectCoreLocalizationDiagnosticEvidence(options: CoreLocalizationDiagnosticOptions | undefined, cause: unknown, onProcessing?: (record: DiagnosticRecord) => unknown) {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreLocalizationDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; }
  catch { deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record)); }
  return onProcessing === undefined ? selectDiagnosticEvidence(definitions, cause) : selectDiagnosticEvidenceWithReport(definitions, cause, onProcessing);
}
export function observeCoreLocalizationDiagnostic(options: CoreLocalizationDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown, fallback?: CoreLocalizationDiagnosticContext) {
  const processing: DiagnosticRecord[] = [];
  const selected = selectCoreLocalizationDiagnosticEvidence(options, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(coreLocalizationDiagnosticDefinitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreLocalizationDiagnosticContext;
  if (detail === undefined) return { ...selected, diagnosticRecord: selected.diagnosticRecord ?? checked };
  const context = Object.freeze({ operation: detail.operation, ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, context)); };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  for (const record of processing) deliver(record);
  return selected;
}
/** One actual call. Positive guard evidence is emitted before legacy error formatting. */
export class LocalizationObservation {
  private phase: CoreLocalizationBoundaryDetail["phase"] = "input-projection";
  private field: CoreLocalizationBoundaryDetail["field"] | undefined;
  private validationRecord: DiagnosticRecord | undefined;
  constructor(readonly operation: CoreLocalizationBoundaryDetail["operation"], private readonly options: CoreLocalizationDiagnosticOptions | undefined) {}
  at<T>(phase: CoreLocalizationBoundaryDetail["phase"], field: CoreLocalizationBoundaryDetail["field"] | undefined, action: () => T): T {
    const previousPhase = this.phase, previousField = this.field;
    this.phase = phase; this.field = field;
    const value = action();
    this.phase = previousPhase; this.field = previousField;
    return value;
  }
  read<T>(field: CoreLocalizationBoundaryDetail["field"], action: () => T): T { return this.at(this.phase, field, action); }
  validation(field: CoreLocalizationValidationDetail["field"], reason: CoreLocalizationValidationDetail["reason"]): void {
    const record = requireDiagnosticRecord(coreLocalizationDiagnosticDefinitions, captureDiagnosticRecord(() => coreLocalizationValidationDiagnosticRecord({ operation: this.operation as CoreLocalizationValidationDetail["operation"], field, reason, effect: "predicate-rejected" })));
    this.validationRecord = record;
    observeCoreLocalizationDiagnostic(this.options, record, undefined, { operation: this.operation, field });
  }
  rejects(field: CoreLocalizationValidationDetail["field"], reason: CoreLocalizationValidationDetail["reason"], action: () => boolean): boolean {
    const rejected = this.at("predicate-invocation", field, action);
    if (rejected) this.validation(field, reason);
    return rejected;
  }
  passes(field: CoreLocalizationValidationDetail["field"], reason: CoreLocalizationValidationDetail["reason"], action: () => boolean): boolean {
    const passed = this.at("predicate-invocation", field, action);
    if (!passed) this.validation(field, reason);
    return passed;
  }
  attach<T extends object>(error: T): T {
    return this.validationRecord === undefined ? error : Object.assign(error, { diagnosticRecord: this.validationRecord });
  }
  unsupported(): DiagnosticRecord {
    const record = requireDiagnosticRecord(coreLocalizationDiagnosticDefinitions, captureDiagnosticRecord(() => coreLocalizationUnsupportedDiagnosticRecord({ operation: "format", phase: "implementation-selection", reason: "unsupported-implementation", effect: "format-not-performed" })));
    observeCoreLocalizationDiagnostic(this.options, record, undefined, { operation: "format", phase: "implementation-selection" });
    return record;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      const detail: CoreLocalizationBoundaryDetail = { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason: "threw", effect: "value-not-produced" };
      observeCoreLocalizationDiagnostic(this.options, captureDiagnosticRecord(() => coreLocalizationBoundaryDiagnosticRecord(detail)), cause, detail);
      throw cause;
    }
  }
}
