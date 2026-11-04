import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreAuthnDiagnosticDefinitions, coreAuthnBoundaryDiagnosticRecord, type CoreAuthnBoundaryDetail, type CoreAuthnDiagnosticOptions } from "./diagnostics";

const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional observer. */ } }
}
export function observeCoreAuthnDiagnostic(options: CoreAuthnDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown) {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreAuthnDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Optional definitions. */ }
  const selected = selectDiagnosticEvidence(definitions, cause);
  const checked = selectDiagnosticEvidence(coreAuthnDiagnosticDefinitions, { diagnosticRecord: own }).diagnosticRecord;
  if (checked === undefined) return selected;
  const ownedContext = Object.freeze({ ...checked.detail as CoreAuthnBoundaryDetail, evidence: "owned" as const });
  const sourceContext = Object.freeze({ ...checked.detail as CoreAuthnBoundaryDetail, evidence: "source" as const });
  const deliver = (record: DiagnosticRecord, context: typeof ownedContext | typeof sourceContext): void => { try { isolate(options?.onDiagnostic?.(record, context)); } catch { /* Preserve original work. */ } };
  deliver(checked, ownedContext);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord, sourceContext);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record, sourceContext);
  return selected;
}
export class PrincipalObservation {
  private phase: CoreAuthnBoundaryDetail["phase"] = "input-projection";
  private field: CoreAuthnBoundaryDetail["field"] = "id";
  constructor(private readonly options: CoreAuthnDiagnosticOptions | undefined) {}
  at<T>(phase: CoreAuthnBoundaryDetail["phase"], field: CoreAuthnBoundaryDetail["field"], action: () => T): T {
    const previousPhase = this.phase, previousField = this.field;
    this.phase = phase; this.field = field;
    const result = action();
    this.phase = previousPhase; this.field = previousField;
    return result;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      observeCoreAuthnDiagnostic(this.options, coreAuthnBoundaryDiagnosticRecord({ operation: "principal", phase: this.phase, field: this.field, reason: "threw", effect: "value-not-produced" }), cause);
      throw cause;
    }
  }
}
