import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";

export const testEntityValidationDiagnostic = defineDiagnostic({
  code: "entity-smoke.test-entity.validation-failed", version: 1,
  classification: { failureKind: "validation", failureSource: "user", severity: "warning", recovery: "user_correctable" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["input", "integerValue", "uuidValue", "occurredAt", "label", "status", "enabled", "categories", "notes", "description", "reviewedAt", "secondaryCategories"] },
    reason: { type: "enum", values: ["missing", "wrong-type", "invalid-format", "invalid-value", "invalid-item"] },
  } },
} as const);

export const testEntityStoredRecordDiagnostic = defineDiagnostic({
  code: "entity-smoke.test-entity.stored-record-invalid", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["id", "attributes", "visibility", "timestamps", "lifecycle", "row-count"] },
    reason: { type: "enum", values: ["invalid-shape"] },
    effect: { type: "enum", values: ["not-returned"] },
  } },
} as const);

export const testEntityIdentifierConflictDiagnostic = defineDiagnostic({
  code: "entity-smoke.test-entity.identifier-conflict", version: 1,
  classification: { failureKind: "conflict", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create"] },
    effect: { type: "enum", values: ["not-created"] },
  } },
} as const);

export const testEntityDiagnosticCatalog = { owner: "entity-smoke.test-entity", definitions: [testEntityValidationDiagnostic, testEntityStoredRecordDiagnostic, testEntityIdentifierConflictDiagnostic] } as const;

export function testEntityValidationRecord(field: "input" | "integerValue" | "uuidValue" | "occurredAt" | "label" | "status" | "enabled" | "categories" | "notes" | "description" | "reviewedAt" | "secondaryCategories", reason: "missing" | "wrong-type" | "invalid-format" | "invalid-value" | "invalid-item"): DiagnosticRecord {
  const result = createDiagnosticRecord(testEntityValidationDiagnostic, { field, reason });
  if (!result.ok) throw new TypeError("TEST_ENTITY_DIAGNOSTIC_INVALID");
  return result.value;
}
