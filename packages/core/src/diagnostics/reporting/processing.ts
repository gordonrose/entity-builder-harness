import { defineDiagnostic, type DiagnosticDefinition } from "../definition";
import { createDiagnosticRecord, inspectDiagnosticEvidence, type DiagnosticEvidence, type DiagnosticRecord, type DiagnosticSelectionStatus } from "../record";
import { deliverDiagnosticRecord } from "./delivery";

const reasons = ["construction-rejected", "construction-threw", "evidence-rejected",
  "definition-unselected", "evidence-inaccessible", "definition-selection-failed"] as const;
export type DiagnosticProcessingReason = typeof reasons[number];
const createFixedRecord = createDiagnosticRecord;
let prepared: {
  readonly definition: DiagnosticDefinition;
  readonly records: ReadonlyMap<DiagnosticProcessingReason, DiagnosticRecord>;
} | undefined;

// Lazy construction avoids the retained descriptor/index initialization cycle.
// The catalogue warms these fixed records before consumers process failures.
function preparation() {
  if (prepared !== undefined) return prepared;
  const definition = defineDiagnostic({
    code: "core.diagnostics.processing-failed", version: 1,
    classification: { failureKind: "bug", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { reason: { type: "enum", values: reasons } } },
  } as const);
  const records = new Map<DiagnosticProcessingReason, DiagnosticRecord>();
  for (const reason of reasons) {
    const checked = createFixedRecord(definition, { reason });
    if (!checked.ok) throw new TypeError("DIAGNOSTIC_PROCESSING_DEFINITION_INVALID");
    records.set(reason, checked.value);
  }
  prepared = { definition, records };
  return prepared;
}

export function diagnosticProcessingDefinition(): DiagnosticDefinition {
  return preparation().definition;
}

/** Returns a prevalidated fixed record, without inspecting the rejected input. */
export function diagnosticProcessingRecord(reason: DiagnosticProcessingReason): DiagnosticRecord {
  const record = preparation().records.get(reason);
  if (record === undefined) throw new TypeError("DIAGNOSTIC_PROCESSING_REASON_INVALID");
  return record;
}

/** Does not retry the builder or reclassify the original operation's failure. */
export function captureDiagnosticRecord(build: () => DiagnosticRecord | undefined): DiagnosticRecord {
  preparation();
  try { return build() ?? diagnosticProcessingRecord("construction-rejected"); }
  catch { return diagnosticProcessingRecord("construction-threw"); }
}

function failureReason(status: DiagnosticSelectionStatus): DiagnosticProcessingReason | undefined {
  return status === "rejected" ? "evidence-rejected"
    : status === "inaccessible" ? "evidence-inaccessible"
      : status === "unselected" ? "definition-unselected" : undefined;
}

/** Required owned evidence must not silently turn into an optional omission. */
export function requireDiagnosticRecord(definitions: readonly DiagnosticDefinition[], record: DiagnosticRecord): DiagnosticRecord {
  // Only our exact prevalidated objects bypass capability selection, not a
  // caller-supplied object merely claiming the same processing code.
  if ([...preparation().records.values()].includes(record)) return record;
  const selected = inspectDiagnosticEvidence(definitions, { diagnosticRecord: record });
  return selected.evidence.diagnosticRecord
    ?? diagnosticProcessingRecord(failureReason(selected.primary) ?? "construction-rejected");
}

/** Source selection remains restrictive; explicitly unselected external evidence is not a missing owned mapping. */
export function selectDiagnosticEvidenceWithReport(
  definitions: readonly DiagnosticDefinition[], source: unknown,
  report: (record: DiagnosticRecord) => unknown,
): DiagnosticEvidence {
  const inspected = inspectDiagnosticEvidence(definitions, source);
  const outcomes = [inspected.primary, inspected.companions.status, ...inspected.companions.entries];
  const reported = new Set<DiagnosticProcessingReason>();
  for (const outcome of outcomes) {
    const reason = failureReason(outcome);
    if (reason === undefined || outcome === "unselected" || reported.has(reason)) continue;
    reported.add(reason);
    deliverDiagnosticRecord(diagnosticProcessingRecord(reason), report);
  }
  return inspected.evidence;
}
