import { coreDiagnosticCatalog } from "@kanbien/core";
import { selectDiagnosticEvidence, type DiagnosticDefinition, type DiagnosticRecord } from "@kanbien/core/diagnostics";
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
const nativeThen = Promise.prototype.then;
function isolate(value: unknown): void {
  if (value === undefined) return;
  try { Reflect.apply(nativeThen, value, [undefined, () => undefined]); }
  catch { try { Reflect.apply(nativeThen, Promise.resolve(value), [undefined, () => undefined]); } catch { /* Optional sink. */ } }
}
/** Independent own/source9 delivery, never a mutation of the thrown value. */
export function observePlatformOperationalDiagnostic(options: PlatformOperationalDiagnosticOptions | undefined, own: DiagnosticRecord, cause?: unknown): void {
  try {
    const checked = selectDiagnosticEvidence([platformOperationalBoundaryDiagnosticDefinition, platformOperationalEventDiagnosticDefinition], { diagnosticRecord: own }).diagnosticRecord;
    if (checked === undefined) return;
    let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformContractDiagnosticCatalog.definitions];
    try { definitions = [...definitions, ...(options?.diagnosticDefinitions ?? [])]; } catch { /* Trusted built-ins remain available. */ }
    const selected = selectDiagnosticEvidence(definitions, cause);
    const detail = checked.detail as Pick<PlatformOperationalDiagnosticContext, "operation" | "phase">;
    const deliver = (record: DiagnosticRecord, evidence: PlatformOperationalDiagnosticContext["evidence"]): void => {
      try { isolate(options?.onDiagnostic?.(record, Object.freeze({ operation: detail.operation, phase: detail.phase, evidence }))); } catch { /* Keep original result and identity. */ }
    };
    deliver(checked, "owned");
    if (selected.diagnosticRecord !== undefined) deliver(selected.diagnosticRecord, "source");
    for (const record of selected.relatedDiagnosticRecords ?? []) deliver(record, "source");
  } catch { /* Observation is optional. */ }
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
      observePlatformOperationalDiagnostic(this.options, platformOperationalBoundaryDiagnosticRecord({ operation: this.operation, phase: this.phase, field: this.field, effect: this.effect }), cause);
      throw cause;
    }
  }
}
