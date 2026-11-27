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
const persistenceCommandCodes = ["persistence.credential-rejected", "persistence.runtime-permission-denied", "persistence.transport-unavailable", "persistence.operation-timed-out", "persistence.unclassified-failure"] as const;
export const persistenceObservedPhases = ["pool_connect", "pool_query", "query", "authentication_value", "tcp_probe", "tls_probe", "unknown"] as const;
export const persistenceFailureClassifications = [
  "authentication_rejected", "authentication_material_invalid", "permission_denied", "content_unavailable",
  "tls_trust_invalid", "transport_unavailable", "timeout", "conflict", "constraint", "transaction_rolled_back", "validation", "query_canceled", "unknown",
] as const;
const historicalPersistenceOperations = ["connect", "readiness", "transaction", "migration", "create_outbox", "write_facts", "write_atomic", "read_outbox", "list_outbox", "claim_outbox", "publish_outbox", "read_processing", "claim_processing", "complete_processing", "release_processing", "append_lineage", "read_lineage"] as const;
export const persistenceOperations = [...historicalPersistenceOperations, "administration", "restore_verification"] as const;
const persistenceScheduleOperations = ["create_schedule", "read_schedule", "list_due_schedules", "handover_schedule"] as const;
const persistenceScheduleControlOperations = ["block_schedule", "resume_schedule"] as const;
const persistenceCurrentOperations = [...persistenceOperations] as const;

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
  detail: { ...historicalDetail, properties: { ...historicalDetail.properties, operation: { type: "enum", values: persistenceCurrentOperations } } },
} as const));
/** Schedule operations extend, rather than rewrite, the established v2 records. */
export const persistenceScheduleDiagnosticDefinitions = persistenceDiagnosticDefinitions.map((definition) => defineDiagnostic({
  ...definition, version: persistenceCommandCodes.includes(definition.code as (typeof persistenceCommandCodes)[number]) ? 5 : 4,
  classification: { ...definition.classification, failureSource: definition.code === "persistence.trust-validation-failed" ? "unknown" : definition.classification.failureSource },
  detail: { ...historicalDetail, properties: { ...historicalDetail.properties, operation: { type: "enum", values: [...persistenceOperations, ...persistenceScheduleOperations] } } },
} as const));
export const persistenceScheduleControlDiagnosticDefinitions = persistenceDiagnosticDefinitions.map((definition) => defineDiagnostic({
  ...definition, version: 6,
  classification: { ...definition.classification, failureSource: definition.code === "persistence.trust-validation-failed" ? "unknown" : definition.classification.failureSource },
  detail: { ...historicalDetail, properties: { ...historicalDetail.properties, operation: { type: "enum", values: persistenceScheduleControlOperations } } },
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

/** Schedule-store rejections are separate so historical local-rejection v1 stays unchanged. */
export const persistenceScheduleRejectionDiagnostic = defineDiagnostic({ code: "persistence.schedule-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create", "list-due", "handover"] },
    field: { type: "enum", values: ["id", "limit", "schedule", "outbox-entry"] },
    condition: { type: "enum", values: ["duplicate", "not-found", "not-integer", "not-positive", "too-large"] },
    effect: { type: "enum", values: ["local-state-unchanged"] },
  } },
} as const);
export type PersistenceScheduleRejectionDetail = NonNullable<typeof persistenceScheduleRejectionDiagnostic.__detail>;
export function persistenceScheduleRejectionDiagnosticRecord(detail: PersistenceScheduleRejectionDetail) { return requiredRecord(persistenceScheduleRejectionDiagnostic, detail); }

/** Durable schedule-store conflicts are distinct from the in-memory proof's known local effect. */
export const persistenceScheduleStoreRejectionDiagnostic = defineDiagnostic({ code: "persistence.schedule-store-rejected", version: 1,
  classification: { failureKind: "conflict", failureSource: "provider", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create"] },
    field: { type: "enum", values: ["id"] },
    condition: { type: "enum", values: ["duplicate"] },
    effect: { type: "enum", values: ["unknown"] },
  } },
} as const);
export type PersistenceScheduleStoreRejectionDetail = NonNullable<typeof persistenceScheduleStoreRejectionDiagnostic.__detail>;
export function persistenceScheduleStoreRejectionDiagnosticRecord(detail: PersistenceScheduleStoreRejectionDetail) { return requiredRecord(persistenceScheduleStoreRejectionDiagnostic, detail); }

const scheduleStoredDetail = { type: "object", properties: {
    operation: { type: "enum", values: ["create", "read", "list-due", "handover"] },
    reduction: { type: "enum", values: ["returned", "null"] },
    effect: { type: "enum", values: ["unknown", "not-assessed"] },
    field: { type: "enum", values: ["row", "id", "job-name", "due-at", "state", "outbox-entry"] },
    condition: { type: "enum", values: ["absent", "invalid"] },
  } } as const;
/** Schedule rows are a new stored shape, so the older generic v1 record vocabulary remains fixed. */
export const persistenceScheduleStoredRecordDiagnostic = defineDiagnostic({ code: "persistence.schedule-stored-record-observed", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: scheduleStoredDetail,
} as const);
export type PersistenceScheduleStoredRecordDetail = NonNullable<typeof persistenceScheduleStoredRecordDiagnostic.__detail>;
export function persistenceScheduleStoredRecordDiagnosticRecord(detail: PersistenceScheduleStoredRecordDetail) { return requiredRecord(persistenceScheduleStoredRecordDiagnostic, detail); }
export const persistenceScheduleControlStoredRecordDiagnostic = defineDiagnostic({
  ...persistenceScheduleStoredRecordDiagnostic, version: 2,
  detail: { ...scheduleStoredDetail, properties: {
    ...scheduleStoredDetail.properties,
    operation: { type: "enum", values: ["block", "resume"] },
  } },
} as const);
export type PersistenceScheduleControlStoredRecordDetail = NonNullable<typeof persistenceScheduleControlStoredRecordDiagnostic.__detail>;
export function persistenceScheduleControlStoredRecordDiagnosticRecord(detail: PersistenceScheduleControlStoredRecordDetail) {
  return requiredRecord(persistenceScheduleControlStoredRecordDiagnostic, detail);
}

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
const commandCodes = persistenceCommandCodes;
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

/** Dispatch owns its work bound, not lease settings or schedule-store limits. */
export const persistenceScheduleDispatchConfigurationDiagnostic = defineDiagnostic({ code: "persistence.schedule-dispatch-configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["maximum-relay-attempts"] },
    reason: { type: "enum", values: ["missing", "wrong-type", "not-finite", "not-integer", "not-positive", "too-large"] },
  } },
} as const);
export type PersistenceScheduleDispatchConfigurationDetail = NonNullable<typeof persistenceScheduleDispatchConfigurationDiagnostic.__detail>;
export function persistenceScheduleDispatchConfigurationDiagnosticRecord(reason: PersistenceScheduleDispatchConfigurationDetail["reason"]) {
  return requiredRecord(persistenceScheduleDispatchConfigurationDiagnostic, { field: "maximum-relay-attempts", reason });
}

/** Observes only the outer call; dependency failures retain their own evidence. */
export const persistenceScheduleDispatchBoundaryDiagnostic = defineDiagnostic({ code: "persistence.schedule-dispatch-boundary-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    boundary: { type: "enum", values: ["continuation-check", "due-delivery", "outbox-relay"] },
    reason: { type: "enum", values: ["threw", "returned-failure"] },
    effect: { type: "enum", values: ["dispatch-not-started", "due-outcome-unknown", "due-success-returned", "relay-outcome-unknown", "relay-success-returned"] },
  } },
} as const);
export type PersistenceScheduleDispatchBoundaryDetail = NonNullable<typeof persistenceScheduleDispatchBoundaryDiagnostic.__detail>;
export function persistenceScheduleDispatchBoundaryDiagnosticRecord(detail: PersistenceScheduleDispatchBoundaryDetail) {
  return requiredRecord(persistenceScheduleDispatchBoundaryDiagnostic, detail);
}

export const persistenceScheduleDeliveryConfigurationDiagnostic = defineDiagnostic({ code: "persistence.schedule-delivery-configuration-invalid", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["maximum-schedules"] },
    reason: { type: "enum", values: ["wrong-type", "not-finite", "not-integer", "not-positive", "too-large"] },
  } },
} as const);
export type PersistenceScheduleDeliveryConfigurationDetail = NonNullable<typeof persistenceScheduleDeliveryConfigurationDiagnostic.__detail>;
export function persistenceScheduleDeliveryConfigurationDiagnosticRecord(reason: PersistenceScheduleDeliveryConfigurationDetail["reason"]) {
  return requiredRecord(persistenceScheduleDeliveryConfigurationDiagnostic, { field: "maximum-schedules", reason });
}

export const persistenceScheduleDeliveryBoundaryDiagnostic = defineDiagnostic({ code: "persistence.schedule-delivery-boundary-observed", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    boundary: { type: "enum", values: ["continuation-check", "clock", "selection", "entry-construction", "handover", "block-unavailable-job"] },
    reason: { type: "enum", values: ["threw", "returned-failure"] },
    effect: { type: "enum", values: ["handover-not-started", "handover-outcome-unknown", "handover-success-returned"] },
  } },
} as const);
export type PersistenceScheduleDeliveryBoundaryDetail = NonNullable<typeof persistenceScheduleDeliveryBoundaryDiagnostic.__detail>;
export function persistenceScheduleDeliveryBoundaryDiagnosticRecord(detail: PersistenceScheduleDeliveryBoundaryDetail) {
  return requiredRecord(persistenceScheduleDeliveryBoundaryDiagnostic, detail);
}

export const persistenceScheduleControlRejectionDiagnostic = defineDiagnostic({ code: "persistence.schedule-control-rejected", version: 1,
  classification: { failureKind: "conflict", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["block", "resume"] },
    condition: { type: "enum", values: ["not-found"] },
    effect: { type: "enum", values: ["no-matching-schedule"] },
  } },
} as const);
export function persistenceScheduleControlRejectionDiagnosticRecord(operation: "block" | "resume") {
  return requiredRecord(persistenceScheduleControlRejectionDiagnostic, { operation, condition: "not-found", effect: "no-matching-schedule" });
}

export const persistenceScheduleJobMappingDiagnostic = defineDiagnostic({ code: "persistence.schedule-job-mapping-rejected", version: 1,
  classification: { failureKind: "configuration", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    reason: { type: "enum", values: ["duplicate-job", "invalid-job-name", "invalid-message-type", "job-unavailable"] },
    effect: { type: "enum", values: ["outbox-not-constructed"] },
  } },
} as const);
export type PersistenceScheduleJobMappingDetail = NonNullable<typeof persistenceScheduleJobMappingDiagnostic.__detail>;
export function persistenceScheduleJobMappingDiagnosticRecord(reason: PersistenceScheduleJobMappingDetail["reason"]) {
  return requiredRecord(persistenceScheduleJobMappingDiagnostic, { reason, effect: "outbox-not-constructed" });
}

export const persistenceScheduleInvalidRowBlockedDiagnostic = defineDiagnostic({ code: "persistence.schedule-invalid-row-blocked", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["list-due"] },
    effect: { type: "enum", values: ["blocked-awaiting-repair"] },
  } },
} as const);
export function persistenceScheduleInvalidRowBlockedDiagnosticRecord() {
  return requiredRecord(persistenceScheduleInvalidRowBlockedDiagnostic, { operation: "list-due", effect: "blocked-awaiting-repair" });
}

export const persistenceScheduleDeliveryReferenceDiagnostic = defineDiagnostic({ code: "persistence.schedule-delivery-reference-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["payload", "outbox-id", "message-type", "message-version", "tenant", "as-of", "outbox", "schedule-reference", "schedule", "job", "handoff", "due-at"] },
    reason: { type: "enum", values: ["wrong-type", "missing", "empty", "mismatch", "not-found", "invalid-format", "not-due"] },
    effect: { type: "enum", values: ["application-work-not-invoked"] },
  } },
} as const);
export type PersistenceScheduleDeliveryReferenceDetail = NonNullable<typeof persistenceScheduleDeliveryReferenceDiagnostic.__detail>;
export function persistenceScheduleDeliveryReferenceDiagnosticRecord(field: PersistenceScheduleDeliveryReferenceDetail["field"], reason: PersistenceScheduleDeliveryReferenceDetail["reason"]) {
  return requiredRecord(persistenceScheduleDeliveryReferenceDiagnostic, { field, reason, effect: "application-work-not-invoked" });
}

/** A rejected retry instruction cannot start a release mutation. */
export const persistenceProcessingRetryRejectedDiagnostic = defineDiagnostic({
  code: "persistence.processing-retry-rejected", version: 1,
  classification: { failureKind: "validation", failureSource: "platform", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["released-at", "retry-at"] },
    reason: { type: "enum", values: ["invalid-timestamp", "before-release"] },
    effect: { type: "enum", values: ["not-started"] },
  } },
} as const);

export const persistenceProcessingRetryStoredInvalidDiagnostic = defineDiagnostic({
  code: "persistence.processing-retry-stored-invalid", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    field: { type: "enum", values: ["retry-at"] },
    reason: { type: "enum", values: ["wrong-type", "invalid-timestamp"] },
    effect: { type: "enum", values: ["not-assessed"] },
  } },
} as const);

/** Subject columns are additive; retain the historical stored-row vocabulary. */
export const persistenceScheduleSubjectDiagnostic = defineDiagnostic({ code: "persistence.schedule-subject-invalid", version: 1,
  classification: { failureKind: "data_integrity", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: {
    operation: { type: "enum", values: ["create", "read", "list-due", "handover", "block", "resume"] },
    field: { type: "enum", values: ["subject-kind", "subject-id", "subject-pair"] },
    condition: { type: "enum", values: ["invalid", "partial"] },
    effect: { type: "enum", values: ["unknown", "not-assessed"] },
  } },
} as const);
export type PersistenceScheduleSubjectDetail = NonNullable<typeof persistenceScheduleSubjectDiagnostic.__detail>;
export function persistenceScheduleSubjectDiagnosticRecord(detail: PersistenceScheduleSubjectDetail) {
  return requiredRecord(persistenceScheduleSubjectDiagnostic, detail);
}

export const platformPersistenceDiagnosticCatalog = { owner: "persistence", definitions: [persistenceScheduleJobMappingDiagnostic, persistenceScheduleControlRejectionDiagnostic, ...persistenceScheduleControlDiagnosticDefinitions, persistenceScheduleDeliveryConfigurationDiagnostic, persistenceScheduleDeliveryBoundaryDiagnostic, persistenceProcessingRetryStoredInvalidDiagnostic, persistenceProcessingRetryRejectedDiagnostic, persistenceScheduleSubjectDiagnostic, persistenceScheduleDispatchConfigurationDiagnostic, persistenceScheduleDispatchBoundaryDiagnostic, ...persistenceLeasingDiagnosticCatalog.definitions, ...persistenceMaintenanceDiagnosticCatalog.definitions, ...persistenceDiagnosticDefinitions, ...persistenceCurrentDiagnosticDefinitions, ...persistenceScheduleDiagnosticDefinitions,
  ...persistenceCrudDiagnosticDefinitions, persistenceConfigurationDiagnostic, persistenceLocalRejectionDiagnostic, persistenceStoredRecordDiagnostic, persistenceBoundaryDiagnostic,
  persistenceReconciliationDiagnostic, ...persistenceCommandDiagnosticDefinitions, persistenceCommandConditionDiagnostic, persistenceStoredAttributeDiagnostic, persistenceStateReconciliationDiagnostic,
  persistenceRelayBoundaryDiagnostic, persistenceConfigurationInputDiagnostic, persistenceScheduleRejectionDiagnostic,
  persistenceScheduleStoreRejectionDiagnostic, persistenceScheduleStoredRecordDiagnostic, persistenceScheduleControlStoredRecordDiagnostic,
  persistenceScheduleDeliveryReferenceDiagnostic, persistenceScheduleInvalidRowBlockedDiagnostic] } as const;

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
}, operation: (typeof persistenceCurrentOperations)[number] | (typeof persistenceScheduleOperations)[number] | (typeof persistenceScheduleControlOperations)[number]) {
  const code = observedCode(facts.classification);
  const effect = operation === "connect" ? "not-started" : ["readiness", "restore_verification", "read_outbox", "list_outbox", "read_processing", "read_lineage", "read_schedule", "list_due_schedules"].includes(operation) ? "not-assessed" : "unknown";
  if (operation === "block_schedule" || operation === "resume_schedule") {
    const definition = persistenceScheduleControlDiagnosticDefinitions.find(item => item.code === code)!;
    return requiredRecord(definition, { phase: facts.phase, classification: facts.classification, codeStatus: facts.code_status, operation, effect });
  }
  const definitions = persistenceScheduleOperations.includes(operation as (typeof persistenceScheduleOperations)[number])
    ? persistenceScheduleDiagnosticDefinitions
    : persistenceCurrentDiagnosticDefinitions;
  const definition = definitions.find((item) => item.code === code)!;
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
