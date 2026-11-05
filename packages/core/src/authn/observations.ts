import { coreDiagnosticCatalog } from "../diagnostic-catalog";
import { captureDiagnosticRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, diagnosticProcessingRecord, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";
import { coreAuthnDiagnosticDefinitions, coreAuthnBoundaryDiagnosticRecord, type CoreAuthnBoundaryDetail, type CoreAuthnDiagnosticOptions } from "./diagnostics";

export function observeCoreAuthnDiagnostic(options: CoreAuthnDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown, fallback?: CoreAuthnBoundaryDetail) {
  const processing: DiagnosticRecord[] = [];
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...coreAuthnDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { processing.push(diagnosticProcessingRecord("definition-selection-failed")); }
  const selected = selectDiagnosticEvidenceWithReport(definitions, cause, record => { processing.push(record); });
  const checked = requireDiagnosticRecord(coreAuthnDiagnosticDefinitions, own);
  const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as CoreAuthnBoundaryDetail;
  if (detail === undefined) return { ...selected, diagnosticRecord: selected.diagnosticRecord ?? checked };
  const ownedContext = Object.freeze({ ...detail, evidence: "owned" as const });
  const sourceContext = Object.freeze({ ...detail, evidence: "source" as const });
  const deliver = (record: DiagnosticRecord, context: typeof ownedContext | typeof sourceContext): void => { deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, context)); };
  deliver(checked, ownedContext);
  if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord, sourceContext);
  for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record, sourceContext);
  for (const record of processing) deliver(record, ownedContext);
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
      const detail: CoreAuthnBoundaryDetail = { operation: "principal", phase: this.phase, field: this.field, reason: "threw", effect: "value-not-produced" };
      observeCoreAuthnDiagnostic(this.options, captureDiagnosticRecord(() => coreAuthnBoundaryDiagnosticRecord(detail)), cause, detail);
      throw cause;
    }
  }
}
