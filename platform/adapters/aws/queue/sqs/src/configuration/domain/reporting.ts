import { coreConfigDiagnosticDefinitions, coreQueueDiagnosticDefinitions, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecords, diagnosticProcessingRecord,
  type CoreQueueDiagnosticOptions, type DiagnosticRecord, type DiagnosticDefinition } from "@kanbien/core";
import { sqsConfigurationDiagnosticCatalog } from "../contract/reporting/diagnostics";

const context = Object.freeze({ operation: "client-initialization", boundary: "selection" } as const);
export function observeSqsConfiguration(options: CoreQueueDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown): void {
  const checked = requireDiagnosticRecord(sqsConfigurationDiagnosticCatalog.definitions, own);
  const notices: DiagnosticRecord[] = [];
  let definitions: readonly DiagnosticDefinition[] = [...coreConfigDiagnosticDefinitions, ...coreQueueDiagnosticDefinitions];
  try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; }
  catch { notices.push(diagnosticProcessingRecord("definition-selection-failed")); }
  const selected = selectDiagnosticEvidenceWithReport(definitions, cause, record => notices.push(record));
  deliverDiagnosticRecords([checked, ...(selected.diagnosticRecord === undefined ? [] : [selected.diagnosticRecord]), ...(selected.relatedDiagnosticRecords ?? []), ...notices],
    record => options?.onDiagnostic?.(record, context));
}
