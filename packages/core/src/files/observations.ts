import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, parseRelatedDiagnosticRecords, captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreFileDiagnosticDefinitions, coreFileBoundaryDiagnosticRecord, coreFileOperationDiagnosticRecord, coreFileValidationDiagnosticRecord, type CoreFileBoundaryDetail, type CoreFileDiagnosticContext, type CoreFileDiagnosticOptions, type CoreFileDiagnosticEvidence, type CoreFileOperationDetail, type CoreFileValidationDetail } from "./diagnostics";

export function selectCoreFileDiagnosticEvidence(options: CoreFileDiagnosticOptions | undefined, cause: unknown, onProcessing?: (record: DiagnosticRecord) => unknown) {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreFileDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; }
  catch { deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record)); }
  return onProcessing === undefined ? selectDiagnosticEvidence(definitions, cause) : selectDiagnosticEvidenceWithReport(definitions, cause, onProcessing);
}
export function observeCoreFileDiagnostic(options: CoreFileDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown, fallback?: CoreFileDiagnosticContext) {
  const processing: DiagnosticRecord[] = [];
  const selected = selectCoreFileDiagnosticEvidence(options, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(coreFileDiagnosticDefinitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreFileDiagnosticContext;
  if (detail === undefined) return { ...selected, diagnosticRecord: selected.diagnosticRecord ?? checked };
  const context = Object.freeze({ operation: detail.operation, ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, context)); };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  for (const record of processing) deliver(record);
  return selected;
}
export function selectedFileCompanions(evidence: CoreFileDiagnosticEvidence | undefined): readonly DiagnosticRecord[] | undefined {
  if (evidence === undefined) return undefined;
  try {
    const definitions = Object.getOwnPropertyDescriptor(evidence, "relatedDiagnosticDefinitions");
    const records = Object.getOwnPropertyDescriptor(evidence, "relatedDiagnosticRecords");
    if (definitions === undefined || !("value" in definitions) || records === undefined || !("value" in records)) return undefined;
    const selected = parseRelatedDiagnosticRecords(definitions.value, records.value);
    return selected.ok ? selected.value : undefined;
  } catch { return undefined; }
}

/** One current invocation: older errors never establish current guard provenance. */
export class FileObservation {
  private phase: CoreFileBoundaryDetail["phase"] = "input-projection";
  private field: CoreFileBoundaryDetail["field"] | undefined;
  private effect: CoreFileBoundaryDetail["effect"] = "value-not-produced";
  reason: CoreFileValidationDetail["reason"] = "predicate-rejected";
  private ordinal: number | undefined;
  mismatch: CoreFileOperationDetail["field"] = "id";
  constructor(readonly operation: CoreFileBoundaryDetail["operation"], private readonly options: CoreFileDiagnosticOptions | undefined) {}
  at<T>(phase: CoreFileBoundaryDetail["phase"], field: CoreFileBoundaryDetail["field"] | undefined, action: () => T): T {
    const previousPhase = this.phase, previousField = this.field;
    this.phase = phase; this.field = field;
    const value = action();
    this.phase = previousPhase; this.field = previousField;
    return value;
  }
  read<T>(field: CoreFileBoundaryDetail["field"], action: () => T): T { return this.at(this.phase, field, action); }
  location(phase: CoreFileBoundaryDetail["phase"], field?: CoreFileBoundaryDetail["field"]): void { this.phase = phase; this.field = field; }
  argument<T>(phase: CoreFileBoundaryDetail["phase"], effect: CoreFileBoundaryDetail["effect"], value: T): T {
    this.location(phase); this.effectIs(effect); return value;
  }
  test(reason: CoreFileValidationDetail["reason"], action: () => boolean, ordinal?: number): boolean {
    const rejected = this.at("predicate-invocation", this.field, action);
    if (rejected && this.reason === "predicate-rejected") { this.reason = reason; this.ordinal = ordinal; }
    return rejected;
  }
  check(field: CoreFileValidationDetail["field"], reason: CoreFileValidationDetail["reason"], action: () => boolean): boolean {
    return this.at("predicate-invocation", field, () => this.test(reason, action));
  }
  equal(field: CoreFileOperationDetail["field"], action: () => boolean): boolean {
    const same = this.at("predicate-invocation", field, action);
    if (!same) this.mismatch = field;
    return same;
  }
  effectIs(effect: CoreFileBoundaryDetail["effect"]): void { this.effect = effect; }
  validation<T extends object>(error: T, field: CoreFileValidationDetail["field"]): T {
    const record = requireDiagnosticRecord(coreFileDiagnosticDefinitions, captureDiagnosticRecord(() => coreFileValidationDiagnosticRecord({ operation: this.operation as CoreFileValidationDetail["operation"], field, reason: this.reason, effect: "rejected", ...(this.ordinal === undefined ? {} : { ordinal: this.ordinal }) })));
    observeCoreFileDiagnostic(this.options, record, undefined, { operation: this.operation, field });
    return Object.assign(error, { diagnosticRecord: record });
  }
  decision<T extends object>(error: T, reason: CoreFileOperationDetail["reason"], field: CoreFileOperationDetail["field"]): T {
    const record = requireDiagnosticRecord(coreFileDiagnosticDefinitions, captureDiagnosticRecord(() => coreFileOperationDiagnosticRecord({ operation: this.operation as CoreFileOperationDetail["operation"], reason, field, effect: "rejected-before-write" })));
    observeCoreFileDiagnostic(this.options, record, undefined, { operation: this.operation, field });
    return Object.assign(error, { diagnosticRecord: record });
  }
  boundary(cause: unknown): ReturnType<typeof selectCoreFileDiagnosticEvidence> {
    const detail: CoreFileBoundaryDetail = { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason: "threw", effect: this.effect };
    const record = requireDiagnosticRecord(coreFileDiagnosticDefinitions, captureDiagnosticRecord(() => coreFileBoundaryDiagnosticRecord(detail)));
    const selected = observeCoreFileDiagnostic(this.options, record, cause, detail);
    return selected.diagnosticRecord === undefined ? { ...selected, diagnosticRecord: record } : selected;
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.boundary(cause); throw cause; } }
}
