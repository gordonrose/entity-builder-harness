import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreLoggingBoundaryDiagnosticRecord, type CoreLoggingBoundaryDetail, type CoreLoggingDiagnosticContext, type CoreLoggingDiagnosticOptions } from "./diagnostics";
export function selectCoreLoggingDiagnosticEvidence(options: CoreLoggingDiagnosticOptions | undefined, cause: unknown) {
  let definitions: readonly DiagnosticDefinition[] = coreDiagnosticCatalog.definitions;
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Optional selection. */ }
  return selectDiagnosticEvidence(definitions, cause);
}
const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional sink. */ } }
}
export function observeCoreLoggingDiagnostic(options: CoreLoggingDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown) {
  const selected = selectCoreLoggingDiagnosticEvidence(options, cause);
  const checked = selectCoreLoggingDiagnosticEvidence(options, { diagnosticRecord: own }).diagnosticRecord;
  if (checked?.code !== "core.logging.boundary-failed") return selected;
  const detail = checked.detail as CoreLoggingDiagnosticContext;
  const context = Object.freeze({ operation: detail.operation, phase: detail.phase, ...(detail.field === undefined ? {} : { field: detail.field }) });
  const deliver = (record: DiagnosticRecord): void => { try { isolate(options?.onDiagnostic?.(record, context)); } catch { /* Preserve receiver/workload. */ } };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
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
    observeCoreLoggingDiagnostic(this.options, coreLoggingBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, ...(this.field === undefined ? {} : { field: this.field }), reason, effect: this.effect }), cause);
  }
  run<T>(action: () => T): T { try { return action(); } catch (cause) { this.failed(cause, "threw"); throw cause; } }
  returned(value: unknown): void {
    if (value === undefined) return;
    const rejected = (cause: unknown): void => this.failed(cause, "rejected");
    try { Reflect.apply(nativeThen, value, [undefined, rejected]); }
    catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, rejected]); } catch { /* Observation cannot change write's void outcome. */ } }
  }
}
