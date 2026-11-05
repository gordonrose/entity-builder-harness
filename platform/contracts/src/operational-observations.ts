import { coreDiagnosticCatalog } from "@kanbien/core";
import { captureDiagnosticRecord, deliverDiagnosticRecord, diagnosticProcessingRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformContractDiagnosticCatalog, platformOperationalBoundaryDiagnosticDefinition, platformOperationalEventDiagnosticDefinition,
  platformOperationalBoundaryDiagnosticRecord, type PlatformOperationalBoundaryDiagnosticDetail } from "./registration-diagnostics";

export interface PlatformOperationalDiagnosticContext {
  readonly operation: PlatformOperationalBoundaryDiagnosticDetail["operation"];
  readonly phase: PlatformOperationalBoundaryDiagnosticDetail["phase"] | "validation";
  readonly evidence: "owned" | "source";
}
export interface PlatformOperationalDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord, context: PlatformOperationalDiagnosticContext) => unknown;
}
/** Independent own/source9 delivery, never a mutation of the thrown value. */
export function observePlatformOperationalDiagnostic(options: PlatformOperationalDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown,
  fallback?: Pick<PlatformOperationalDiagnosticContext, "operation" | "phase">): void {
    const checked = requireDiagnosticRecord([platformOperationalBoundaryDiagnosticDefinition, platformOperationalEventDiagnosticDefinition], own);
    const detail = checked.code === "core.diagnostics.processing-failed" ? fallback : checked.detail as Pick<PlatformOperationalDiagnosticContext, "operation" | "phase">;
    if (detail === undefined) return;
    const notices: DiagnosticRecord[] = [];
    let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformContractDiagnosticCatalog.definitions];
    try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { notices.push(diagnosticProcessingRecord("definition-selection-failed")); }
    const selected = selectDiagnosticEvidenceWithReport(definitions, cause, record => notices.push(record));
    const deliver = (record: DiagnosticRecord, evidence: PlatformOperationalDiagnosticContext["evidence"]): void => {
      deliverDiagnosticRecord(record, value => options?.onDiagnostic?.(value, Object.freeze({ operation: detail.operation, phase: detail.phase, evidence })));
    };
    deliver(checked, "owned");
    if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord, "source");
    for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record, "source");
    for (const record of notices) deliver(record, "owned");
}
export class PlatformOperationalObservation {
  private phase: PlatformOperationalBoundaryDiagnosticDetail["phase"];
  private field: PlatformOperationalBoundaryDiagnosticDetail["field"];
  constructor(private readonly operation: PlatformOperationalBoundaryDiagnosticDetail["operation"],
    private readonly effect: PlatformOperationalBoundaryDiagnosticDetail["effect"], private readonly options?: PlatformOperationalDiagnosticOptions) {
    this.phase = operation === "readiness-event" ? "structure" : "snapshot";
    this.field = operation === "readiness-event" ? "event" : "flags";
  }
  location(phase: PlatformOperationalBoundaryDiagnosticDetail["phase"], field: PlatformOperationalBoundaryDiagnosticDetail["field"]): void { this.phase = phase; this.field = field; }
  at<T>(phase: PlatformOperationalBoundaryDiagnosticDetail["phase"], field: PlatformOperationalBoundaryDiagnosticDetail["field"], action: () => T): T {
    const previousPhase = this.phase, previousField = this.field;
    this.location(phase, field);
    const result = action();
    this.location(previousPhase, previousField);
    return result;
  }
  run<T>(action: () => T): T {
    try { return action(); } catch (cause) {
      const detail = { operation: this.operation, phase: this.phase, field: this.field, effect: this.effect };
      observePlatformOperationalDiagnostic(this.options, captureDiagnosticRecord(() => platformOperationalBoundaryDiagnosticRecord(detail)), cause, detail);
      throw cause;
    }
  }
}
