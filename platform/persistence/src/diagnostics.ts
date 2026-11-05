import { persistenceMaintenanceDiagnosticCatalog } from "./maintenance/index";
import { persistenceLeasingDiagnosticCatalog } from "./leasing/index";
import { coreDiagnosticCatalog } from "@kanbien/core";
import { configReasonNames } from "@kanbien/core/config";
import { captureDiagnosticRecord, createDiagnosticRecord, defineDiagnostic, diagnosticProcessingRecord, requireDiagnosticRecord, selectDiagnosticEvidenceWithReport, deliverDiagnosticRecord, deliverDiagnosticRecords, type DiagnosticDefinition, type DiagnosticEvidence, type DiagnosticRecord, type FailureKind } from "@kanbien/core/diagnostics";

/** Canonical runtime identities; deployment mappings consume this export. */
export const persistenceDiagnosticCodes = [
  "persistence.transport-unavailable", "persistence.trust-validation-failed", "persistence.credential-rejected",
  "persistence.runtime-permission-denied", "persistence.capacity-exhausted", "persistence.schema-incompatible",
  "persistence.operation-timed-out", "persistence.outcome-uncertain", "persistence.unclassified-failure",
] as const;
export const persistenceObservedPhases = ["pool_connect", "pool_query", "query", "authentication_value", "tcp_probe", "tls_probe", "unknown"] as const;
export const persistenceFailureClassifications = [
  "authentication_rejected", "authentication_material_invalid", "permission_denied", "content_unavailable",
  "tls_trust_invalid", "transport_unavailable", "timeout", "conflict", "constraint", "transaction_rolled_back", "validation", "query_canceled", "unknown",
] as const;
const historicalPersistenceOperations = ["connect", "readiness", "transaction", "migration", "create_outbox", "write_facts", "write_atomic", "read_outbox", "list_outbox", "claim_outbox", "publish_outbox", "read_processing", "claim_processing", "complete_processing", "release_processing", "append_lineage", "read_lineage"] as const;
export const persistenceOperations = [...historicalPersistenceOperations, "administration", "restore_verification"] as const;

const kinds: Record<(typeof persistenceDiagnosticCodes)[number], FailureKind> = {
  "persistence.transport-unavailable": "dependency_unavailable", "persistence.trust-validation-failed": "configuration",
  "persistence.credential-rejected": "authentication", "persistence.runtime-permission-denied": "authorization",
  "persistence.capacity-exhausted": "dependency_unavailable", "persistence.schema-incompatible": "data_integrity",
  "persistence.operation-timed-out": "timeout", "persistence.outcome-uncertain": "unknown", "persistence.unclassified-failure": "unknown",
};

const historicalDetail = { type: "object", properties: {
    phase: { type: "enum", values: persistenceObservedPhases },
    classification: { type: "enum", values: persistenceFailureClassifications },
    codeStatus: { type: "enum", values: ["recognized", "unrecognized", "absent"] },
    operation: { type: "enum", values: historicalPersistenceOperations },
    effect: { type: "enum", values: ["not-started", "unknown", "not-assessed"] },
  } } as const;
export const persistenceDiagnosticDefinitions = persistenceDiagnosticCodes.map((code) => defineDiagnostic({ code, version: 1,
  classification: { failureKind: kinds[code],
    failureSource: "provider", severity: "error", recovery: "manual_investigation" },
  detail: historicalDetail,
} as const));
/** Historical v1 remains readable; TLS verification never establishes provider fault. */
export const persistenceCurrentDiagnosticDefinitions = persistenceDiagnosticDefinitions.map((definition) => defineDiagnostic({
  ...definition, version: 2,
  classification: { ...definition.classification, failureSource: definition.code === "persistence.trust-validation-failed" ? "unknown" : "provider" },
  detail: { ...historicalDetail, properties: { ...historicalDetail.properties, operation: { type: "enum", values: persistenceOperations } } },
} as const));
/** Store bindings contain no provider names, addresses, or submitted identifiers. */
export const persistenceConfigurationDiagnostic = defineDiagnostic({ code: "persistence.configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["region", "store", "outbox-index", "lineage-index", "configuration"] },
    reason: { type: "enum", values: ["blank", "too-long"] },
  } },
} as const);
export function persistenceConfigurationDiagnosticRecord(field: "region" | "store" | "outbox-index" | "lineage-index" | "configuration", reason: "blank" | "too-long") {
  const checked = createDiagnosticRecord(persistenceConfigurationDiagnostic, { field, reason });
  if (!checked.ok) throw new TypeError("PERSISTENCE_CONFIGURATION_DIAGNOSTIC_INVALID");
  return checked.value;
}
export const persistenceConfigurationInputDiagnostic = defineDiagnostic({ code: "persistence.configuration-input-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["region", "store", "outbox-index", "lineage-index", "configuration"] },
    reason: { type: "enum", values: [configReasonNames.missing, configReasonNames.wrongType, configReasonNames.wrongShape] },
  } },
} as const);
export function persistenceConfigurationInputDiagnosticRecord(
  field: "region" | "store" | "outbox-index" | "lineage-index" | "configuration", reason: "missing" | "wrong-type" | "wrong-shape",
) {
  return requiredRecord(persistenceConfigurationInputDiagnostic, { field, reason });
}
export const persistenceLocalRejectionDiagnostic = defineDiagnostic({ code: "persistence.local-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: [...persistenceOperations, "validate-mutation", "validate-lease", "stage-statement", "validate-identifier"] },
    field: { type: "enum", values: ["subject-kind", "subject-id", "causation", "tenant", "correlation", "owner", "fence", "attempt", "duration", "expiry", "sequence", "limit", "record", "state", "lease", "tool-version", "schema", "schema-preprovisioned", "migration-id", "checksum", "statements", "statement", "transaction", "participant", "mutation", "after-commit", "identifier", "manifest"] },
    condition: { type: "enum", values: ["mismatch", "left-absent", "right-absent", "pattern", "not-integer", "not-positive", "negative", "not-after-acquisition", "cannot-advance", "not-found", "wrong-state", "absent", "stale", "expired", "duplicate", "too-large", "wrong-type", "empty", "out-of-order", "blank", "nul", "untrimmed", "too-long", "semicolon", "unsupported-verb", "closed", "unsupported", "missing", "checksum-mismatch", "predicate-rejected"] },
    phase: { type: "enum", values: ["validation", "preflight", "state-check", "statement-selection", "transaction-body", "after-statements"] },
    effect: { type: "enum", values: ["not-started", "local-state-unchanged", "unknown", "not-assessed"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
  }, optional: ["ordinal"] },
} as const);
export type PersistenceLocalRejectionDetail = NonNullable<typeof persistenceLocalRejectionDiagnostic.__detail>;
export function persistenceLocalRejectionDiagnosticRecord(detail: PersistenceLocalRejectionDetail) { return requiredRecord(persistenceLocalRejectionDiagnostic, detail); }

export const persistenceStoredRecordDiagnostic = defineDiagnostic({ code: "persistence.stored-record-observed", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: persistenceOperations },
    reduction: { type: "enum", values: ["null", "filtered", "duplicate", "returned", "thrown", "reconciled-state"] },
    effect: { type: "enum", values: ["not-assessed", "unknown"] },
    issues: { type: "array", minItems: 1, maxItems: 16, items: { type: "object", properties: {
    field: { type: "enum", values: ["row", "id", "subject-kind", "subject-id", "message-type", "message-version", "delivery-policy", "attempt", "lease", "owner", "fence", "expiry", "completion", "record-kind", "record-id", "revision", "actor", "changed-fields", "record-change", "identifier"] },
    condition: { type: "enum", values: ["absent", "invalid", "partial", "all-null", "required", "nullness-mismatch", "not-integer", "not-positive", "negative", "pattern", "empty", "untrimmed", "duplicate", "too-many", "not-after-acquisition"] },
    ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
    count: { type: "integer", minimum: 1, maximum: Number.MAX_SAFE_INTEGER },
    }, optional: ["ordinal", "count"] } },
    truncated: { type: "boolean" },
  } },
} as const);
export type PersistenceStoredRecordDetail = NonNullable<typeof persistenceStoredRecordDiagnostic.__detail>;
export function persistenceStoredRecordDiagnosticRecord(detail: PersistenceStoredRecordDetail) { return requiredRecord(persistenceStoredRecordDiagnostic, detail); }

export const persistenceBoundaryDiagnostic = defineDiagnostic({ code: "persistence.boundary-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: [...persistenceOperations, "connection-pool", "transaction-client"] },
    phase: { type: "enum", values: ["invocation", "completion", "event", "returned-result"] },
    boundary: { type: "enum", values: ["acquire", "begin", "body", "commit", "rollback", "recovery-rollback", "release", "idle-pool", "end", "after-commit", "expiry-normalization", "decode", "reconciliation"] },
    condition: { type: "enum", values: ["threw", "rejected", "returned-failure", "unsupported"] },
    effect: { type: "enum", values: ["not-started", "unknown", "not-assessed", "transaction-open", "rollback-completed", "commit-completed"] },
    reconciliation: { type: "enum", values: ["lease-present-fence-matched"] },
  }, optional: ["reconciliation"] },
} as const);
export type PersistenceBoundaryDetail = NonNullable<typeof persistenceBoundaryDiagnostic.__detail>;
export function persistenceBoundaryDiagnosticRecord(detail: PersistenceBoundaryDetail) { return requiredRecord(persistenceBoundaryDiagnostic, detail); }

/** A read establishes observed state, never ownership or outcome of a prior write. */
export const persistenceReconciliationDiagnostic = defineDiagnostic({ code: "persistence.reconciliation-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create"] },
    primaryOutcome: { type: "enum", values: ["no-row-returned", "call-threw"] },
    observed: { type: "enum", values: ["matching", "different", "absent", "unavailable"] },
    effect: { type: "enum", values: ["read-result-observed"] },
  } },
} as const);
export type PersistenceReconciliationDetail = NonNullable<typeof persistenceReconciliationDiagnostic.__detail>;
export function persistenceReconciliationDiagnosticRecord(detail: PersistenceReconciliationDetail) { return requiredRecord(persistenceReconciliationDiagnostic, detail); }

/** CRUD is additive: historical v1/v2 operation arrays remain exact. */
export const persistenceCrudDiagnosticDefinitions = persistenceCurrentDiagnosticDefinitions.map((definition) => defineDiagnostic({ ...definition, version: 3,
  classification: { ...definition.classification, failureSource: definition.code === "persistence.unclassified-failure" ? "unknown" : definition.classification.failureSource },
  detail: { ...historicalDetail, properties: { ...historicalDetail.properties,
    operation: { type: "enum", values: ["create", "read", "delete"] },
    boundary: { type: "enum", values: ["primary", "reconciliation"] },
    effect: { type: "enum", values: ["unknown", "not-assessed"] },
  } },
} as const));

export const persistenceCommandConditions = ["access-rejected", "identity-unrecognized", "credential-expired", "condition-rejected", "transaction-canceled",
  "resource-unavailable", "input-rejected", "throughput-exceeded", "request-limit-exceeded", "throttled", "timeout", "network-failure", "unclassified"] as const;
const commandCodeStatuses = ["not-inspected", "absent", "wrong-type", "unavailable", "recognized", "unrecognized"] as const;
const commandDetail = { type: "object", properties: {
  operation: { type: "enum", values: [...persistenceOperations, "client-initialization"] },
  boundary: { type: "enum", values: ["client-construction", "selection", "encoding", "invocation", "response", "decoding", "callback"] },
  role: { type: "enum", values: ["primary", "reconciliation"] },
  condition: { type: "enum", values: persistenceCommandConditions },
  codeStatus: { type: "enum", values: commandCodeStatuses },
  effect: { type: "enum", values: ["not-invoked", "unknown", "not-assessed"] },
  cancellation: { type: "object", properties: {
    availability: { type: "enum", values: ["absent", "wrong-type", "unavailable", "available"] },
    truncated: { type: "boolean" },
    reasons: { type: "array", minItems: 0, maxItems: 64, items: { type: "object", properties: {
      ordinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
      codeStatus: { type: "enum", values: commandCodeStatuses },
      condition: { type: "enum", values: persistenceCommandConditions },
    } } },
  } },
}, optional: ["cancellation"] } as const;
const commandCodes = ["persistence.credential-rejected", "persistence.runtime-permission-denied", "persistence.transport-unavailable", "persistence.operation-timed-out", "persistence.unclassified-failure"] as const;
export const persistenceCommandDiagnosticDefinitions = commandCodes.map((code) => defineDiagnostic({ code, version: 4,
  classification: { failureKind: kinds[code], failureSource: code === "persistence.unclassified-failure" ? "unknown" : "provider", severity: "error", recovery: "manual_investigation" },
  detail: commandDetail,
} as const));
/** A rejected condition is an observed SDK fact, not a failed workflow. */
export const persistenceCommandConditionDiagnostic = defineDiagnostic({ code: "persistence.command-condition-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: commandDetail,
} as const);
export type PersistenceCommandObservationDetail = NonNullable<(typeof persistenceCommandDiagnosticDefinitions)[number]["__detail"]>;
export function persistenceCommandDiagnosticRecord(detail: PersistenceCommandObservationDetail) {
  if (detail.boundary === "invocation" && detail.codeStatus === "recognized" && detail.condition === "condition-rejected") {
    return requiredRecord(persistenceCommandConditionDiagnostic, detail);
  }
  const code = detail.boundary !== "invocation" || detail.codeStatus !== "recognized" ? "persistence.unclassified-failure"
    : detail.condition === "access-rejected" ? "persistence.runtime-permission-denied"
    : detail.condition === "identity-unrecognized" || detail.condition === "credential-expired" ? "persistence.credential-rejected"
    : detail.condition === "network-failure" ? "persistence.transport-unavailable"
    : detail.condition === "timeout" ? "persistence.operation-timed-out" : "persistence.unclassified-failure";
  return requiredRecord(persistenceCommandDiagnosticDefinitions.find((definition) => definition.code === code)!, detail);
}

export const persistenceStoredAttributeDiagnostic = defineDiagnostic({ code: "persistence.stored-attribute-observed", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: persistenceOperations },
    reduction: { type: "enum", values: ["null", "empty-list", "filtered", "thrown", "returned"] },
    effect: { type: "enum", values: ["unknown", "not-assessed"] },
    issues: { type: "array", minItems: 1, maxItems: 16, items: { type: "object", properties: {
      field: { type: "enum", values: ["response", "item", "items", "attribute", "outboxEntryId", "subjectKind", "subjectId", "messageType", "messageVersion", "deliveryPolicy", "createdAt", "tenantId", "correlationId", "causationId", "state", "attempt", "leaseOwner", "leaseFence", "leaseAcquiredAt", "leaseExpiresAt", "publishedAt", "releasedAt", "completionOutcome", "completedAt", "recordChangeId", "recordKind", "recordId", "revision", "action", "occurredAt", "actorKind", "actorId", "actor", "changedFields", "lease", "completion"] },
      condition: { type: "enum", values: ["absent", "null", "not-object", "not-array", "string-component-absent", "number-component-absent", "not-safe-integer", "invalid-format", "closed-value-rejected", "incomplete", "contract-rejected", "too-many", "duplicate", "empty", "untrimmed", "not-positive", "negative", "not-integer", "not-after-acquisition", "predicate-rejected"] },
      rowOrdinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
      attributeOrdinal: { type: "integer", minimum: 0, maximum: Number.MAX_SAFE_INTEGER },
      count: { type: "integer", minimum: 1, maximum: Number.MAX_SAFE_INTEGER },
    }, optional: ["rowOrdinal", "attributeOrdinal", "count"] } },
    truncated: { type: "boolean" },
  } },
} as const);
export type PersistenceStoredAttributeDetail = NonNullable<typeof persistenceStoredAttributeDiagnostic.__detail>;
export function persistenceStoredAttributeDiagnosticRecord(detail: PersistenceStoredAttributeDetail) { return requiredRecord(persistenceStoredAttributeDiagnostic, detail); }

export const persistenceStateReconciliationDiagnostic = defineDiagnostic({ code: "persistence.reconciliation-observed", version: 2,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "info", recovery: "not_recoverable", action: "none" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["claim_outbox", "publish_outbox", "claim_processing", "complete_processing", "release_processing"] },
    primaryOutcome: { type: "enum", values: ["condition-rejected"] },
    observed: { type: "enum", values: ["missing", "already-published", "lease-active", "already-completed", "valid-current-state", "unresolved", "unavailable"] },
    effect: { type: "enum", values: ["read-result-observed"] },
  } },
} as const);
export type PersistenceStateReconciliationDetail = NonNullable<typeof persistenceStateReconciliationDiagnostic.__detail>;
export function persistenceStateReconciliationDiagnosticRecord(detail: PersistenceStateReconciliationDetail) { return requiredRecord(persistenceStateReconciliationDiagnostic, detail); }

export const persistenceRelayBoundaryDiagnostic = defineDiagnostic({ code: "persistence.relay-boundary-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["run-once", "queue-message"] },
    boundary: { type: "enum", values: ["claim-clock", "claim-time-normalization", "list-deliverable", "candidate-selection", "claim", "envelope-construction", "queue-send", "publication-clock", "publication-time-normalization", "publish-marker", "result-projection"] },
    reason: { type: "enum", values: ["threw", "returned-failure"] },
    effect: { type: "enum", values: ["relay-send-not-invoked", "send-outcome-unknown", "send-success-marker-not-invoked", "send-success-marker-outcome-unknown", "marker-success-returned"] },
  } },
} as const);
export type PersistenceRelayBoundaryDetail = NonNullable<typeof persistenceRelayBoundaryDiagnostic.__detail>;
export function persistenceRelayBoundaryDiagnosticRecord(detail: PersistenceRelayBoundaryDetail) { return requiredRecord(persistenceRelayBoundaryDiagnostic, detail); }

export const platformPersistenceDiagnosticCatalog = { owner: "persistence", definitions: [...persistenceLeasingDiagnosticCatalog.definitions, ...persistenceMaintenanceDiagnosticCatalog.definitions, ...persistenceDiagnosticDefinitions, ...persistenceCurrentDiagnosticDefinitions,
  ...persistenceCrudDiagnosticDefinitions, persistenceConfigurationDiagnostic, persistenceLocalRejectionDiagnostic, persistenceStoredRecordDiagnostic, persistenceBoundaryDiagnostic,
  persistenceReconciliationDiagnostic, ...persistenceCommandDiagnosticDefinitions, persistenceCommandConditionDiagnostic, persistenceStoredAttributeDiagnostic, persistenceStateReconciliationDiagnostic,
  persistenceRelayBoundaryDiagnostic, persistenceConfigurationInputDiagnostic] } as const;

export interface PlatformPersistenceDiagnosticOptions {
  readonly diagnosticDefinitions?: readonly DiagnosticDefinition[];
  readonly onDiagnostic?: (record: DiagnosticRecord) => unknown;
}
/** A supplied invocation owns its observer; even {} silences shared defaults. */
export function resolvePlatformPersistenceDiagnosticOptions(defaults: PlatformPersistenceDiagnosticOptions | undefined,
  invocation?: PlatformPersistenceDiagnosticOptions): PlatformPersistenceDiagnosticOptions {
  if (invocation === undefined) return defaults ?? {};
  const owner = invocation;
  let definitions: readonly DiagnosticDefinition[] = [];
  const unavailable = () => deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => owner.onDiagnostic?.(record));
  try { definitions = [...(defaults?.diagnosticDefinitions ?? [])]; } catch { unavailable(); }
  try { definitions = [...definitions, ...(invocation.diagnosticDefinitions ?? [])]; } catch { unavailable(); }
  return Object.freeze({ diagnosticDefinitions: Object.freeze(definitions), onDiagnostic(record: DiagnosticRecord) {
    return deliverDiagnosticRecord(record, selected => owner?.onDiagnostic?.(selected));
  } });
}
export function selectPlatformPersistenceDiagnosticEvidence(options: PlatformPersistenceDiagnosticOptions, cause: unknown, onProcessing?: (record: DiagnosticRecord) => unknown): DiagnosticEvidence {
  let definitions: readonly DiagnosticDefinition[] = [...coreDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions];
  try { definitions = [...definitions, ...(options.diagnosticDefinitions ?? [])]; }
  catch { deliverDiagnosticRecord(diagnosticProcessingRecord("definition-selection-failed"), record => onProcessing?.(record)); }
  return selectDiagnosticEvidenceWithReport(definitions, cause, record => onProcessing?.(record));
}
/** Apply the shared processing guard without moving persistence meanings to Core. */
export function capturePlatformPersistenceDiagnostic(build: () => DiagnosticRecord | undefined): DiagnosticRecord {
  return requireDiagnosticRecord([...coreDiagnosticCatalog.definitions, ...platformPersistenceDiagnosticCatalog.definitions], captureDiagnosticRecord(build));
}
/** The independent location never displaces any of the source's primary/eight. */
export function observePlatformPersistenceDiagnostic(options: PlatformPersistenceDiagnosticOptions | undefined, ownRecord: DiagnosticRecord, cause?: unknown): DiagnosticEvidence {
  const notices: DiagnosticRecord[] = [];
  const selected = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, cause, record => notices.push(record));
  const own = selectPlatformPersistenceDiagnosticEvidence(options ?? {}, { diagnosticRecord: ownRecord }).diagnosticRecord
    ?? capturePlatformPersistenceDiagnostic(() => ownRecord);
  deliverDiagnosticRecords([own,
    ...(selected.diagnosticRecord === undefined ? [] : [selected.diagnosticRecord]), ...(selected.relatedDiagnosticRecords ?? []), ...notices],
    record => options?.onDiagnostic?.(record));
  return own.code === "core.diagnostics.processing-failed" ? { ...selected, diagnosticRecord: selected.diagnosticRecord ?? own } : selected;
}
function requiredRecord<T>(definition: DiagnosticDefinition<T>, detail: T): DiagnosticRecord<T> {
  const checked = createDiagnosticRecord(definition, detail);
  if (!checked.ok) throw new TypeError("PLATFORM_PERSISTENCE_DIAGNOSTIC_INVALID");
  return checked.value;
}
export function persistenceCrudObservedDiagnosticRecord(facts: Parameters<typeof persistenceObservedDiagnosticRecord>[0], operation: "create" | "read" | "delete", boundary: "primary" | "reconciliation") {
  const definition = persistenceCrudDiagnosticDefinitions.find((item) => item.code === observedCode(facts.classification))!;
  return requiredRecord(definition, { phase: facts.phase, classification: facts.classification, codeStatus: facts.code_status,
    operation, boundary, effect: operation === "read" ? "not-assessed" : "unknown" });
}

/** A provider classification is evidence, not proof of the final write outcome. */
export function persistenceObservedDiagnosticRecord(facts: {
  readonly classification: (typeof persistenceFailureClassifications)[number];
  readonly code_status: "recognized" | "unrecognized" | "absent";
  readonly phase: (typeof persistenceObservedPhases)[number];
}, operation: (typeof persistenceOperations)[number]) {
  const code = observedCode(facts.classification);
  const effect = operation === "connect" ? "not-started" : ["readiness", "restore_verification", "read_outbox", "list_outbox", "read_processing", "read_lineage"].includes(operation) ? "not-assessed" : "unknown";
  const definition = persistenceCurrentDiagnosticDefinitions.find((item) => item.code === code)!;
  const record = createDiagnosticRecord(definition, { phase: facts.phase, classification: facts.classification, codeStatus: facts.code_status, operation, effect });
  if (!record.ok) throw new TypeError("PLATFORM_PERSISTENCE_DIAGNOSTIC_INVALID");
  return record.value;
}
function observedCode(classification: (typeof persistenceFailureClassifications)[number]): (typeof persistenceDiagnosticCodes)[number] {
  return classification === "transport_unavailable" ? "persistence.transport-unavailable"
    : classification === "tls_trust_invalid" ? "persistence.trust-validation-failed"
    : classification === "authentication_rejected" ? "persistence.credential-rejected"
    : classification === "permission_denied" ? "persistence.runtime-permission-denied"
    : classification === "timeout" ? "persistence.operation-timed-out"
    : "persistence.unclassified-failure";
}
