import type { CoreError, MessageDescriptor } from "@kanbien/core/shared";
import { createDiagnosticRecord } from "@kanbien/core/diagnostics";
import { testEntityIdentifierConflictDiagnostic } from "./diagnostics";

export interface TestEntityError extends MessageDescriptor {
  readonly diagnosticRecord?: CoreError["diagnosticRecord"];
  readonly relatedDiagnosticRecords?: CoreError["relatedDiagnosticRecords"];
}

export function testEntityError(code: string, defaultMessage: string, diagnosticRecord?: CoreError["diagnosticRecord"], relatedDiagnosticRecords?: CoreError["relatedDiagnosticRecords"]): TestEntityError {
  return { code, defaultMessage, ...(diagnosticRecord === undefined ? {} : { diagnosticRecord }),
    ...(relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords }) };
}

/** Provider bindings translate a positively identified key collision while
 * retaining their selected source record and complete companion envelope. */
export function testEntityCreationConflict(source?: Pick<CoreError, "diagnosticRecord" | "relatedDiagnosticRecords">): TestEntityError {
  const checked = createDiagnosticRecord(testEntityIdentifierConflictDiagnostic, { operation: "create", effect: "not-created" });
  if (!checked.ok) throw new TypeError("TEST_ENTITY_DIAGNOSTIC_INVALID");
  return { ...testEntityError("TEST_ENTITY_ID_CONFLICT", "The generated test entity ID is already in use.", source?.diagnosticRecord ?? checked.value),
    ...(source?.relatedDiagnosticRecords === undefined ? {} : { relatedDiagnosticRecords: source.relatedDiagnosticRecords }) };
}
