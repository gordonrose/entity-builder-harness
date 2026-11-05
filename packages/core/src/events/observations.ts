import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticRecord } from "../diagnostics/index";
import { attachCoreDiagnosticRecord } from "../shared/diagnostics";
import { coreEventDiagnosticDefinitions, coreEventBoundaryDiagnosticRecord, coreEventValidationDiagnosticRecord,
  type CoreEventBoundaryDetail, type CoreEventDiagnosticContext, type CoreEventDiagnosticOptions, type CoreEventValidationDetail } from "./diagnostics";

export function selectCoreEventDiagnosticDefinitions(options: CoreEventDiagnosticOptions | undefined, onProcessing?: (record: DiagnosticRecord) => unknown) {
  const builtins = [...coreDiagnosticCatalog.definitions, ...coreEventDiagnosticDefinitions];
  try { return [...builtins, ...(options?.diagnosticDefinitions ?? [])]; }
  catch {
    deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record));
    return builtins;
  }
}
function observe(options: CoreEventDiagnosticOptions | undefined, own: DiagnosticRecord, fallback: CoreEventDiagnosticContext, cause?: unknown) {
  const processing: DiagnosticRecord[] = [];
  const definitions = selectCoreEventDiagnosticDefinitions(options, record => { processing.push(record); });
  const selected = selectDiagnosticEvidenceWithReport(definitions, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(definitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreEventDiagnosticContext;
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
  return { definitions, ...(selected.diagnosticRecord === undefined ? checked === undefined ? {} : { diagnosticRecord: checked } : { diagnosticRecord: selected.diagnosticRecord }),
    ...(selected.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: selected.relatedDiagnosticRecords }) };
}
/** Finite capability locations, not a general instrumentation or retry policy. */
export class EventObservation {
  private phase: CoreEventBoundaryDetail["phase"] = "input-projection";
  private field: CoreEventBoundaryDetail["field"] | undefined;
  private effect: CoreEventBoundaryDetail["effect"] = "result-not-returned";
  private handlerEffect: CoreEventBoundaryDetail["handlerEffect"] | undefined;
  private eventOrdinal: number | undefined;
  private handlerOrdinal: number | undefined;
  constructor(private readonly operation: CoreEventBoundaryDetail["operation"], private readonly options: CoreEventDiagnosticOptions | undefined) {}
  location(phase: CoreEventBoundaryDetail["phase"], field?: CoreEventBoundaryDetail["field"]): void { this.phase = phase; this.field = field; }
  effectIs(effect: CoreEventBoundaryDetail["effect"]): void { this.effect = effect; }
  handlerIs(effect: CoreEventBoundaryDetail["handlerEffect"]): void { this.handlerEffect = effect; }
  eventAt(ordinal: number | undefined): void { this.eventOrdinal = ordinal; }
  handlerAt(ordinal: number | undefined): void { this.handlerOrdinal = ordinal; }
  at<T>(phase: CoreEventBoundaryDetail["phase"], field: CoreEventBoundaryDetail["field"] | undefined, action: () => T): T {
    const previousPhase = this.phase, previousField = this.field;
    this.location(phase, field);
    const value = action();
    this.location(previousPhase, previousField);
    return value;
  }
  validation(detail: Omit<CoreEventValidationDetail, "effect">): DiagnosticRecord {
    const own = captureDiagnosticRecord(() => coreEventValidationDiagnosticRecord({ ...detail, effect: "rejected" }));
    return observe(this.options, own, { operation: detail.operation, field: detail.field }).diagnosticRecord!;
  }
  failed(cause: unknown, reason: CoreEventBoundaryDetail["reason"] = "threw") {
    const own = captureDiagnosticRecord(() => coreEventBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, reason, effect: this.effect,
      ...(this.field === undefined ? {} : { field: this.field }), ...(this.handlerEffect === undefined ? {} : { handlerEffect: this.handlerEffect }),
      ...(this.eventOrdinal === undefined ? {} : { eventOrdinal: this.eventOrdinal }), ...(this.handlerOrdinal === undefined ? {} : { handlerOrdinal: this.handlerOrdinal }) }));
    return observe(this.options, own, { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }) }, cause);
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.failed(cause); throw cause; } }
}
