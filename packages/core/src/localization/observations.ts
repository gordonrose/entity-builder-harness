import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreLocalizationDiagnosticDefinitions, coreLocalizationBoundaryDiagnosticRecord, coreLocalizationValidationDiagnosticRecord, coreLocalizationUnsupportedDiagnosticRecord, type CoreLocalizationBoundaryDetail, type CoreLocalizationDiagnosticContext, type CoreLocalizationDiagnosticOptions, type CoreLocalizationValidationDetail } from "./diagnostics";

export function selectCoreLocalizationDiagnosticEvidence(options: CoreLocalizationDiagnosticOptions | undefined, cause: unknown) {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreLocalizationDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Optional selection unavailable. */ }
  return selectDiagnosticEvidence(definitions, cause);
}
const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional observer. */ } }
}
export function observeCoreLocalizationDiagnostic(options: CoreLocalizationDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown) {
  const selected = selectCoreLocalizationDiagnosticEvidence(options, cause);
  const checked = selectCoreLocalizationDiagnosticEvidence(options, { diagnosticRecord: own }).diagnosticRecord;
  if (checked === undefined || !coreLocalizationDiagnosticDefinitions.some((definition) => definition.code === checked.code && definition.version === checked.definitionVersion)) return selected;
  const detail = checked.detail as CoreLocalizationDiagnosticContext;
  const context = Object.freeze({ operation: detail.operation, ...(detail.phase === undefined ? {} : { phase: detail.phase }), ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { try { isolate(options?.onDiagnostic?.(record, context)); } catch { /* Keep original receiver and work. */ } };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
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
    const record = coreLocalizationValidationDiagnosticRecord({ operation: this.operation as CoreLocalizationValidationDetail["operation"], field, reason, effect: "predicate-rejected" });
    this.validationRecord = record;
    observeCoreLocalizationDiagnostic(this.options, record);
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
    const record = coreLocalizationUnsupportedDiagnosticRecord({ operation: "format", phase: "implementation-selection", reason: "unsupported-implementation", effect: "format-not-performed" });
    observeCoreLocalizationDiagnostic(this.options, record);
    return record;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      observeCoreLocalizationDiagnostic(this.options, coreLocalizationBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason: "threw", effect: "value-not-produced" }), cause);
      throw cause;
    }
  }
}
