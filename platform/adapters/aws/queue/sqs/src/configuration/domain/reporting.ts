import { coreConfigDiagnosticDefinitions, coreQueueDiagnosticDefinitions, parseDiagnosticRecord, selectDiagnosticEvidence, deliverDiagnosticRecords,
  type CoreQueueDiagnosticOptions, type DiagnosticRecord, type DiagnosticDefinition } from "@kanbien/core";
import { sqsConfigurationDiagnosticCatalog } from "../contract/reporting/diagnostics";

const context = Object.freeze({ operation: "client-initialization", boundary: "selection" } as const);
export function observeSqsConfiguration(options: CoreQueueDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown): void {
  try {
    const definition = sqsConfigurationDiagnosticCatalog.definitions.find(item => item.code === own.code && item.version === own.definitionVersion);
    if (definition === undefined || !parseDiagnosticRecord<unknown>(definition, own).ok) return;
    let definitions: readonly DiagnosticDefinition[] = [...coreConfigDiagnosticDefinitions, ...coreQueueDiagnosticDefinitions];
    try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Own evidence remains independently available. */ }
    const selected = selectDiagnosticEvidence(definitions, cause);
    deliverDiagnosticRecords([own, ...(selected.diagnosticRecord === undefined ? [] : [selected.diagnosticRecord]), ...(selected.relatedDiagnosticRecords ?? [])],
      record => options?.onDiagnostic?.(record, context));
  } catch { /* Malformed optional evidence never changes workload behavior. */ }
}
