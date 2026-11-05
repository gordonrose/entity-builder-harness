import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreTenancyDiagnosticDefinitions, coreTenancyBoundaryDiagnosticRecord, type CoreTenancyBoundaryDetail, type CoreTenancyDiagnosticOptions } from "./diagnostics";

export function observeCoreTenancyDiagnostic(options: CoreTenancyDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown, fallback?: CoreTenancyBoundaryDetail) {
  const processing: DiagnosticRecord[] = [];
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreTenancyDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { processing.push(diagnosticProcessingRecord("definition-selection-failed")); }
  const selected = selectDiagnosticEvidenceWithReport(definitions, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(coreTenancyDiagnosticDefinitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreTenancyBoundaryDetail;
  if (detail === undefined) return { ...selected, diagnosticRecord: selected.diagnosticRecord ?? checked };
  const deliver = (record: DiagnosticRecord): void => { deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, detail)); };
  deliver(checked);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record);
  for (const record of processing) deliver(record);
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
      const detail: CoreTenancyBoundaryDetail = { operation: "tenant-context", phase: "input-projection", field: this.field, reason: "threw", effect: "value-not-produced" };
      observeCoreTenancyDiagnostic(this.options, captureDiagnosticRecord(() => coreTenancyBoundaryDiagnosticRecord(detail)), cause, detail);
      throw cause;
    }
  }
}
