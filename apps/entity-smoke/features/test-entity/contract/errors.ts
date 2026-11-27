import type { CoreError, MessageDescriptor } from "@kanbien/core/shared";
import { captureDiagnosticRecord, createDiagnosticRecord, requireDiagnosticRecord } from "@kanbien/core/diagnostics";
import { testEntityIdentifierConflictDiagnostic, testEntityRetentionDiagnostic, testEntityWriteConflictDiagnostic } from "./diagnostics";

export interface TestEntityError extends MessageDescriptor {
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly relatedDiagnosticRecords?: CoreError["relatedDiagnosticRecords"];
}

export function testEntityError(code: string, defaultMessage: string, diagnosticRecord?: CoreError["diagnosticRecord"], relatedDiagnosticRecords?: CoreError["relatedDiagnosticRecords"]): TestEntityError {
  return { code, defaultMessage, ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
    ...(relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords }) };
}

export function testEntityRetentionRejected(
  field: "transaction" | "delivery" | "subject" | "entity-id",
  reason: "missing" | "mismatch" | "invalid-format",
): TestEntityError {
  const evidence = requireDiagnosticRecord([testEntityRetentionDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(testEntityRetentionDiagnostic, { field, reason, effect: "mutation-not-invoked" });
    if (!checked.ok) throw checked.error;
    return checked.value;
  }));
  return testEntityError("TEST_ENTITY_RETENTION_REJECTED", "The retention operation could not be validated.", evidence);
}

export function testEntityWriteConflict(): TestEntityError {
  const evidence = requireDiagnosticRecord([testEntityWriteConflictDiagnostic], captureDiagnosticRecord(() => {
    const checked = createDiagnosticRecord(testEntityWriteConflictDiagnostic, { condition: "changed-or-missing", effect: "not-saved" });
    if (!checked.ok) throw checked.error;
    return checked.value;
  }));
  return testEntityError("TEST_ENTITY_WRITE_CONFLICT", "The test entity changed before it could be saved.", evidence);
}

/** Provider bindings translate a positively identified key collision while
 * retaining their selected source record and complete companion envelope. */
export function testEntityCreationConflict(source?: Pick<CoreError, "diagnosticRecord" | "relatedDiagnosticRecords">): TestEntityError {
  const checked = createDiagnosticRecord(testEntityIdentifierConflictDiagnostic, { operation: "create", effect: "not-created" });
  if (!checked.ok) throw new TypeError("TEST_ENTITY_DIAGNOSTIC_INVALID");
  return { ...testEntityError("TEST_ENTITY_ID_CONFLICT", "The generated test entity ID is already in use.", source?.diagnosticRecord ?? checked.value),
    ...(source?.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: source.relatedDiagnosticRecords }) };
}
