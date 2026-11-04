import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { attachCoreDiagnosticRecord } from "../shared/diagnostics";
import { coreAuditDiagnosticDefinitions, coreAuditBoundaryDiagnosticRecord, coreAuditValidationDiagnosticRecord,
  type CoreAuditBoundaryDetail, type CoreAuditDiagnosticContext, type CoreAuditDiagnosticOptions, type CoreAuditValidationDetail } from "./diagnostics";

const nativeThen = Promise.prototype.then;
function observe(options: CoreAuditDiagnosticOptions | undefined, own: DiagnosticRecord | undefined, fallback: CoreAuditDiagnosticContext, cause?: unknown) {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreAuditDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Keep trusted definitions. */ }
  const selected = selectDiagnosticEvidence(definitions, cause);
  const checked = selectDiagnosticEvidence(definitions, { diagnosticRecord: own }).diagnosticRecord;
  const detail = checked?.detail as CoreAuditDiagnosticContext | undefined ?? fallback;
  const context = Object.freeze({ operation: detail.operation,
    ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => {
    try {
      const value = options?.onDiagnostic?.(record, context);
      if (value === undefined) return;
      try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
      catch { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); }
    } catch { /* Preserve original work, receiver and thrown value. */ }
  };
  if (checked !== undefined) deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
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
  validation(detail: Omit<CoreAuditValidationDetail, "effect">): DiagnosticRecord | undefined {
    let own: DiagnosticRecord | undefined;
    try { own = coreAuditValidationDiagnosticRecord({ ...detail, effect: "rejected" }); } catch { /* Optional evidence. */ }
    observe(this.options, own, { operation: detail.operation, field: detail.field });
    return own;
  }
  failed(cause: unknown) {
    let own: DiagnosticRecord | undefined;
    try { own = coreAuditBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, reason: "threw", effect: this.effect,
      ...(this.field === undefined ? {} : { field: this.field }), ...(this.ordinal === undefined ? {} : { ordinal: this.ordinal }) }); } catch { /* Independently preserve source. */ }
    return observe(this.options, own, { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }) }, cause);
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.failed(cause); throw cause; } }
}
