import { createDiagnosticRecord, defineDiagnostic, type DiagnosticDefinition, type DiagnosticRecord } from "../diagnostics/index";

/** These are the existing Core predicates, not submitted values or storage policy. */
export const corePersistenceValidationDiagnostic = defineDiagnostic({
  code: "core.persistence.validation-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["lifecycle-policy", "retention-reference", "delete", "restore", "record-kind", "record-id", "record-revision", "change-field", "change-actor", "record-change", "outbox-type", "outbox-version", "outbox-policy", "page-total", "page-totals", "page-request", "save"] },
    field: { type: "enum", values: ["recovery-window", "legal-hold-check", "retention-policy", "state", "deleted-at", "restore-boundary", "restore-time", "kind", "id", "revision", "field-name", "actor-id", "changed-fields", "message-type", "message-version", "delivery-policy", "total", "totalItems", "totalMatchingItems", "totals", "limit", "cursor", "transaction", "concurrency-token"] },
    reason: { type: "enum", values: ["not-safe-integer", "not-integer", "not-positive", "negative", "required", "invalid-format", "already-deleted", "invalid-time", "unrepresentable-boundary", "not-deleted", "window-expired", "empty", "untrimmed", "too-many", "duplicate", "matching-exceeds-total", "unsupported", "record-absent", "token-unavailable", "token-mismatch"] },
    effect: { type: "enum", values: ["rejected"] },
  } },
} as const);

/** Effects refer to this helper's statements, never arbitrary callback side effects. */
export const corePersistenceInMemoryBoundaryDiagnostic = defineDiagnostic({
  code: "core.persistence.in-memory-boundary-failed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["initialize", "get", "save", "unit-of-work", "after-commit-registration"] },
    phase: { type: "enum", values: ["get-id", "clone-initial", "clone-read", "get-concurrency-token", "clone-before-write", "clone-after-write", "operation", "after-commit", "closed-registration"] },
    reason: { type: "enum", values: ["boundary-threw", "transaction-closed"] },
    effect: { type: "enum", values: ["write-not-reached", "write-completed", "read-only", "operation-not-returned", "operation-returned", "registration-rejected"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["ordinal"] },
} as const);

export const corePersistenceDiagnosticDefinitions = Object.freeze([
  corePersistenceValidationDiagnostic, corePersistenceInMemoryBoundaryDiagnostic,
]);
export type CorePersistenceValidationDetail = NonNullable<typeof corePersistenceValidationDiagnostic.__detail>;
export type CorePersistenceInMemoryBoundaryDetail = NonNullable<typeof corePersistenceInMemoryBoundaryDiagnostic.__detail>;
/** Independent local evidence cannot displace a source primary plus eight companions. */
export type CorePersistenceDiagnosticObserver = (record: DiagnosticRecord) => unknown;
export interface InMemoryPersistenceDiagnosticOptions {
  readonly onDiagnostic?: CorePersistenceDiagnosticObserver;
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
}
export function corePersistenceValidationRecord(detail: Omit<CorePersistenceValidationDetail, "effect">) {
  const checked = createDiagnosticRecord(corePersistenceValidationDiagnostic, { ...detail, effect: "rejected" });
  if (!checked.ok) throw new TypeError("CORE_PERSISTENCE_DIAGNOSTIC_INVALID");
  return checked.value;
}
export function corePersistenceInMemoryBoundaryRecord(detail: CorePersistenceInMemoryBoundaryDetail) {
  const checked = createDiagnosticRecord(corePersistenceInMemoryBoundaryDiagnostic, detail);
  if (!checked.ok) throw new TypeError("CORE_PERSISTENCE_DIAGNOSTIC_INVALID");
  return checked.value;
}
