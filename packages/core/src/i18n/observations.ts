import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { attachCoreDiagnosticRecord } from "../shared/diagnostics";
import { coreI18nDiagnosticDefinitions, coreI18nBoundaryDiagnosticRecord, coreI18nSelectionDiagnosticRecord, coreI18nValidationDiagnosticRecord,
  type CoreI18nBoundaryDetail, type CoreI18nDiagnosticContext, type CoreI18nDiagnosticOptions, type CoreI18nSelectionDetail, type CoreI18nValidationDetail } from "./diagnostics";

const nativeThen = Promise.prototype.then;
function observe(options: CoreI18nDiagnosticOptions | undefined, own: DiagnosticRecord | undefined, context: CoreI18nDiagnosticContext, cause?: unknown): void {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreI18nDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Explicit selection unavailable. */ }
  const selected = selectDiagnosticEvidence(definitions, cause);
  const checked = selectDiagnosticEvidence(definitions, { diagnosticRecord: own }).diagnosticRecord;
  const fixedContext = Object.freeze({ ...context });
  const deliver = (record: DiagnosticRecord): void => {
    try {
      const returned = options?.onDiagnostic?.(record, fixedContext);
      if (returned === undefined) return;
      try { Reflect.apply(nativeThen, returned, [undefined, () => undefined]); }
      catch { Reflect.apply(nativeThen, Promise.resolve(returned), [undefined, () => undefined]); }
    } catch { /* Preserve the work and its thrown identity, including rejected observers. */ }
  };
  if (checked !== undefined) deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  if (checked !== undefined) attachCoreDiagnosticRecord(cause, checked);
}

/** Invocation-local locations only; never inspect an input again for diagnostics. */
export class I18nObservation {
  private phase: CoreI18nBoundaryDetail["phase"] = "input-projection";
  private field: CoreI18nBoundaryDetail["field"] | undefined;
  private ordinal: number | undefined;
  constructor(private readonly operation: CoreI18nBoundaryDetail["operation"], private readonly options: CoreI18nDiagnosticOptions | undefined) {}
  location(phase: CoreI18nBoundaryDetail["phase"], field?: CoreI18nBoundaryDetail["field"], ordinal?: number): void {
    this.phase = phase; this.field = field; this.ordinal = ordinal;
  }
  at<T>(phase: CoreI18nBoundaryDetail["phase"], field: CoreI18nBoundaryDetail["field"] | undefined, action: () => T, ordinal?: number): T {
    const previousPhase = this.phase, previousField = this.field, previousOrdinal = this.ordinal;
    this.location(phase, field, ordinal);
    const value = action();
    this.location(previousPhase, previousField, previousOrdinal);
    return value;
  }
  argument<T>(phase: CoreI18nBoundaryDetail["phase"], field: CoreI18nBoundaryDetail["field"] | undefined, value: T, ordinal?: number): T {
    this.location(phase, field, ordinal); return value;
  }
  rejected<T>(error: T, detail: Omit<CoreI18nValidationDetail, "effect">): T {
    const own = coreI18nValidationDiagnosticRecord({ ...detail, effect: "predicate-rejected" });
    observe(this.options, own, { operation: detail.operation, field: detail.field });
    return attachCoreDiagnosticRecord(error, own);
  }
  selection(detail: Omit<CoreI18nSelectionDetail, "operation" | "phase" | "effect">): void {
    const own = coreI18nSelectionDiagnosticRecord({ operation: "translate", phase: "source-selection", effect: "source-selected", ...detail });
    observe(this.options, own, { operation: "translate", phase: "source-selection" });
  }
  run<T>(action: () => T): T {
    try { return action(); }
    catch (cause) {
      let own: DiagnosticRecord | undefined;
      try { own = coreI18nBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, reason: "threw", effect: "value-not-produced",
        ...(this.field === undefined ? {} : { field: this.field }), ...(this.ordinal === undefined ? {} : { ordinal: this.ordinal }) }); } catch { /* Retain independently selected source evidence. */ }
      observe(this.options, own, { operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }) }, cause);
      throw cause;
    }
  }
}
