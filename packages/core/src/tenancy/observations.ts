import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreTenancyDiagnosticDefinitions, coreTenancyBoundaryDiagnosticRecord, type CoreTenancyBoundaryDetail, type CoreTenancyDiagnosticOptions } from "./diagnostics";

const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional observer. */ } }
}
export function observeCoreTenancyDiagnostic(options: CoreTenancyDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown) {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreTenancyDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Optional definitions. */ }
  const selected = selectDiagnosticEvidence(definitions, cause);
  const checked = selectDiagnosticEvidence(coreTenancyDiagnosticDefinitions, { diagnosticRecord: own }).diagnosticRecord;
  if (checked === undefined) return selected;
  const deliver = (record: DiagnosticRecord): void => { try { isolate(options?.onDiagnostic?.(record, checked.detail as CoreTenancyBoundaryDetail)); } catch { /* Preserve original work. */ } };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  return selected;
}
export class TenantObservation {
  private field: CoreTenancyBoundaryDetail["field"] = "tenant-id";
  constructor(private readonly options: CoreTenancyDiagnosticOptions | undefined) {}
  read<T>(field: CoreTenancyBoundaryDetail["field"], action: () => T): T {
    const previous = this.field;
    this.field = field;
    const result = action();
    this.field = previous;
    return result;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      observeCoreTenancyDiagnostic(this.options, coreTenancyBoundaryDiagnosticRecord({ operation: "tenant-context", phase: "input-projection", field: this.field, reason: "threw", effect: "value-not-produced" }), cause);
      throw cause;
    }
  }
}
