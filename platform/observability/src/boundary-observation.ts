import { coreDiagnosticCatalog } from "@kanbien/core";
import { captureDiagnosticRecord, requireDiagnosticRecord, diagnosticProcessingRecord, createDiagnosticRecord, selectDiagnosticEvidenceWithReport, validDiagnosticDefinition, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformContractDiagnosticCatalog, type PlatformDiagnosticContext, type PlatformDiagnosticReporter } from "@kanbien/platform-contracts";
import { platformObservabilityDiagnosticCatalog } from "./configuration";
import { reportPlatformDiagnostic } from "./diagnostics";
import { platformObservationBoundaryDiagnostic, type PlatformObservationBoundaryDetail } from "./boundary-definitions";

export interface PlatformObservationDiagnostics {
  readonly reporter?: PlatformDiagnosticReporter;
  readonly definitions?: readonly DiagnosticDefinition[];
  readonly context: PlatformDiagnosticContext;
}
const reporting = new WeakSet<PlatformDiagnosticReporter>();
/** Independent own/source delivery; no failed logger fallback, await, replay or record eviction. */
export function reportPlatformObservationBoundary(options: PlatformObservationDiagnostics | undefined,
  detail: PlatformObservationBoundaryDetail, source?: unknown): void {
  reportObservation(options, detail, source);
}
/** An existing producer may already own its precise record; do not invent another boundary. */
export function reportPlatformObservationSources(options: PlatformObservationDiagnostics | undefined, source: unknown): void {
  reportObservation(options, undefined, source);
}
function reportObservation(options: PlatformObservationDiagnostics | undefined, detail: PlatformObservationBoundaryDetail | undefined, source: unknown): void {
  let reporter: PlatformDiagnosticReporter | undefined;
  let entered = false;
  try {
    reporter = options?.reporter;
    if (reporter === undefined || reporting.has(reporter)) return;
    const builtins: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformObservabilityDiagnosticCatalog.definitions, ...platformContractDiagnosticCatalog.definitions];
    let definitions = builtins;
    const processing: DiagnosticRecord[] = [];
    try {
      const additional = options?.definitions;
      if (additional !== undefined && Array.isArray(additional) && additional.every(validDiagnosticDefinition)) definitions = [...builtins, ...additional];
      else if (additional !== undefined) processing.push(diagnosticProcessingRecord("definition-selection-failed"));
    } catch { processing.push(diagnosticProcessingRecord("definition-selection-failed")); }
    const context = options!.context;
    // Validate/copy before any injected sink: the default reporter performs this same exact context policy.
    const fields = Object.getOwnPropertyDescriptors(context);
    const keys = Reflect.ownKeys(context).sort().join(",");
    if (Object.getPrototypeOf(context) !== Object.prototype || (keys !== "capability,operation,stage" && keys !== "capability,correlationId,operation,stage")
      || Object.values(fields).some((field) => !("value" in field))) return;
    const copied = Object.fromEntries(Object.entries(fields).map(([key, field]) => [key, field.value])) as unknown as PlatformDiagnosticContext;
    if (![copied.capability, copied.operation].every((value) => typeof value === "string" && /^[a-z][a-z0-9.-]{0,127}$/.test(value))
      || !["configuration", "startup", "runtime", "request", "readiness", "migration", "recovery", "shutdown"].includes(copied.stage)
      || (copied.correlationId !== undefined && (typeof copied.correlationId !== "string" || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(copied.correlationId)))) return;
    const own = detail === undefined ? undefined : requireDiagnosticRecord(definitions, captureDiagnosticRecord(() => {
      const result = createDiagnosticRecord(platformObservationBoundaryDiagnostic, detail);
      return result.ok ? result.value : undefined;
    }));
    const selected = selectDiagnosticEvidenceWithReport(definitions, source, record => { processing.push(record); });
    reporting.add(reporter); entered = true;
    if (own !== undefined) reportPlatformDiagnostic(reporter, own, copied);
    if (selected.diagnosticRecord !== undefined) reportPlatformDiagnostic(reporter, selected.diagnosticRecord, copied);
    for (const record of selected.relatedDiagnosticRecords ?? []) reportPlatformDiagnostic(reporter, record, copied);
    for (const record of processing) reportPlatformDiagnostic(reporter, record, copied);
  } catch { /* Optional diagnostics never replace workload behavior. */ }
  finally { if (entered && reporter !== undefined) reporting.delete(reporter); }
}
