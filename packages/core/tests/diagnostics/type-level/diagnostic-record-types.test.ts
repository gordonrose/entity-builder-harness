import { captureDiagnosticRecord, createDiagnosticRecord, defineDiagnostic, diagnosticProcessingRecord, inspectDiagnosticEvidence, requireDiagnosticRecord, selectDiagnosticEvidence, type DiagnosticRecord, type DiagnosticSelectionStatus } from "../../../src/diagnostics";
import { auditRecordError, eventPublishError, fileError, type CoreAuditErrorEvidence, type CoreError } from "../../../src/index";

const definition = defineDiagnostic({ code: "type-proof.validation-failed", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "warning", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["enabled", "limit"] },
    reason: { type: "enum", values: ["missing", "wrong-type"] },
    count: { type: "integer", minimum: 0, maximum: 5 },
  }, optional: ["count"] },
} as const);
createDiagnosticRecord(definition, { field: "enabled", reason: "missing" });
createDiagnosticRecord(definition, { field: "limit", reason: "wrong-type", count: 2 });
// @ts-expect-error An undeclared attribute is not a diagnostic field.
createDiagnosticRecord(definition, { field: "password", reason: "missing" });
// @ts-expect-error Raw values cannot be added to a closed diagnostic record.
createDiagnosticRecord(definition, { field: "enabled", reason: "missing", value: "secret" });
// @ts-expect-error Required reasons must be supplied.
createDiagnosticRecord(definition, { field: "enabled" });
// @ts-expect-error Detail types are inferred from the code-owned schema.
createDiagnosticRecord(definition, { field: "enabled", reason: "missing", count: "2" });

const evidence = selectDiagnosticEvidence([definition], new Error("untrusted"));
const primary: DiagnosticRecord | undefined = evidence.diagnosticRecord;
const companions: readonly DiagnosticRecord[] | undefined = evidence.relatedDiagnosticRecords;
void [primary, companions];
// @ts-expect-error The selected detail remains unknown until interpreted by its owner.
const unsafeDetail: { field: string } | undefined = evidence.diagnosticRecord?.detail;
// @ts-expect-error Selected evidence is readonly.
evidence.diagnosticRecord = primary;

const inspection = inspectDiagnosticEvidence([definition], {});
const status: DiagnosticSelectionStatus = inspection.primary;
const required: DiagnosticRecord = requireDiagnosticRecord([definition], captureDiagnosticRecord(() => undefined));
diagnosticProcessingRecord("construction-rejected");
// @ts-expect-error Processing reasons are code-owned, not exception text.
diagnosticProcessingRecord("private native error");
// @ts-expect-error Inspection does not permit callers to rewrite the observed outcome.
inspection.primary = "selected";
// @ts-expect-error Companion outcome positions are readonly.
inspection.companions.entries.push("rejected");
void [status, required];

const legacyErrorInput = { code: "fixture" as never, defaultMessage: "Fixed compatibility fixture." };
type CompanionFactory = (input: typeof legacyErrorInput, evidence?: CoreAuditErrorEvidence) => CoreError;
const companionFactories: readonly CompanionFactory[] = [auditRecordError, eventPublishError, fileError];
for (const factory of companionFactories) {
  factory(legacyErrorInput);
  factory(legacyErrorInput, { relatedDiagnosticDefinitions: [definition], relatedDiagnosticRecords: [] });
  // @ts-expect-error New companions require an explicitly supplied definition set.
  factory(legacyErrorInput, { relatedDiagnosticRecords: [] });
  // @ts-expect-error Native errors are not structured diagnostic companions.
  factory(legacyErrorInput, { relatedDiagnosticDefinitions: [definition], relatedDiagnosticRecords: [new Error("private")] });
}
