import {
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  recordChange,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
  type OutboxEntry,
  type RecordChange,
} from "@kanbien/core/persistence";
import { causationId, isoDateTimeFromDate } from "@kanbien/core/shared";
import {
  createInMemoryPlatformOutboxStore,
  createInMemoryPlatformProcessingStore,
  platformOutboxQueueMessage,
  platformPersistenceFence,
  platformPersistenceLeaseOwner,
  platformPersistenceMutation,
  persistenceLocalRejectionDiagnosticRecord, persistenceStoredRecordDiagnosticRecord, persistenceCrudObservedDiagnosticRecord,
  persistenceCommandDiagnosticRecord, persistenceStoredAttributeDiagnosticRecord, persistenceStateReconciliationDiagnosticRecord,
  type PlatformPersistenceAtomicWriter,
  persistenceRelayBoundaryDiagnosticRecord,
  type PlatformPersistenceMutation,
  type PlatformOutboxQueuePayload,
  type PlatformOutboxStore,
  type PlatformProcessingStore,
} from "../../src/index";

const now = isoDateTimeFromDate(new Date("2026-09-23T12:00:00.000Z"));
const migrationInstructions: import("../../src/index").PersistenceMigrationInstructions = { operation: "apply" };
const connectionInstructions: import("../../src/index").PersistenceVerificationInstructions = { mode: "connection" };
// @ts-expect-error New operations require an explicit maintenance contract change.
const unsupportedMigration: import("../../src/index").PersistenceMigrationInstructions = { operation: "inspect" };
// @ts-expect-error Record verification requires both checked proof fields.
const incompleteRecordVerification: import("../../src/index").PersistenceVerificationInstructions = { mode: "verify-record" };
void migrationInstructions; void connectionInstructions; void unsupportedMigration; void incompleteRecordVerification;
const typeResult = outboxMessageType("platform-smoke.work.accepted");
const policyResult = outboxDeliveryPolicy("platform-short-idempotent-work.v1");
if (!typeResult.ok || !policyResult.ok) {
  throw new Error("Expected valid outbox fixtures.");
}

const entry: OutboxEntry = outboxEntry({
  id: outboxEntryId("outbox-1"),
  subject: recordReference({ kind: accepted(recordKind("platform-smoke.work-item")), id: accepted(recordId("work-1")) }),
  messageType: typeResult.value,
  deliveryPolicy: policyResult.value,
  createdAt: now,
  causationId: causationId("request-1"),
});
const outbox: PlatformOutboxStore = createInMemoryPlatformOutboxStore();
const processing: PlatformProcessingStore = createInMemoryPlatformProcessingStore();

const recordKindResult = recordKind("platform-smoke.work-item");
const recordIdResult = recordId("work-1");
const revisionResult = recordRevision(1);
if (!recordKindResult.ok || !recordIdResult.ok || !revisionResult.ok) {
  throw new Error("Expected valid lineage fixtures.");
}

const change: RecordChange = accepted(recordChange({
  id: recordChangeId("change-1"),
  record: recordReference({ kind: recordKindResult.value, id: recordIdResult.value }),
  revision: revisionResult.value,
  action: "created",
  occurredAt: now,
  causationId: causationId("request-1"),
}));
const mutationResult = platformPersistenceMutation({ recordChange: change, outboxEntry: entry });
if (!mutationResult.ok) {
  throw new Error("Expected valid transactional mutation.");
}
const mutation: PlatformPersistenceMutation = mutationResult.value;

const relayMessageResult = platformOutboxQueueMessage(entry, now);
if (!relayMessageResult.ok) {
  throw new Error("Expected a valid minimal queue envelope.");
}
const relayPayload: PlatformOutboxQueuePayload = relayMessageResult.value.payload;

const ownerResult = platformPersistenceLeaseOwner("worker-a");
const fenceResult = platformPersistenceFence(1);
if (!ownerResult.ok || !fenceResult.ok) {
  throw new Error("Expected valid platform persistence fixtures.");
}

void entry;
void outbox;
void processing;
void change;
void mutation;
void relayPayload;
void ownerResult.value;
void fenceResult.value;
void processing.release({
  outboxEntryId: entry.id,
  fence: fenceResult.value,
  releasedAt: now,
});

// @ts-expect-error outbox entries intentionally do not carry a raw message payload.
const invalidOutboxEntry: OutboxEntry = { ...entry, payload: { email: "private@example.test" } };
void invalidOutboxEntry;

// @ts-expect-error record changes intentionally do not carry unrestricted metadata.
const invalidChange: RecordChange = { ...change, metadata: { oldValue: "private" } };
void invalidChange;

// @ts-expect-error a fence must be a branded persistence fence, not a plain number.
processing.complete({ outboxEntryId: entry.id, fence: 1, outcome: "succeeded", completedAt: now });

// @ts-expect-error a lease owner must be a validated branded identifier.
outbox.claim({ id: entry.id, owner: "worker-a", acquiredAt: now, leaseDurationMs: 1_000 });

// @ts-expect-error processing release requires a branded persistence fence.
processing.release({ outboxEntryId: entry.id, fence: 1, releasedAt: now });

// @ts-expect-error the relay queue payload exposes only the durable outbox identity.
const invalidRelayPayload: PlatformOutboxQueuePayload = { outboxEntryId: "outbox-1", rawPayload: "private" };
void invalidRelayPayload;

persistenceLocalRejectionDiagnosticRecord({ operation: "migration", field: "checksum", condition: "checksum-mismatch", phase: "after-statements", effect: "unknown", ordinal: 1 });
persistenceStoredRecordDiagnosticRecord({ operation: "read_lineage", reduction: "filtered", effect: "not-assessed", issues: [{ field: "revision", condition: "not-positive", count: 2 }], truncated: true });
// @ts-expect-error local diagnostic detail cannot contain submitted values.
persistenceLocalRejectionDiagnosticRecord({ operation: "migration", field: "checksum", condition: "checksum-mismatch", phase: "after-statements", effect: "unknown", value: "private" });
// @ts-expect-error stored diagnostics must explicitly disclose truncation.
persistenceStoredRecordDiagnosticRecord({ operation: "read_lineage", reduction: "filtered", effect: "not-assessed", issues: [{ field: "revision", condition: "not-positive" }] });
// @ts-expect-error target acceptance names do not belong in the portable native operation vocabulary.
persistenceCrudObservedDiagnosticRecord({ phase: "query", classification: "timeout", code_status: "recognized" }, "acceptance-insert", "primary");
const compatibleWriter: PlatformPersistenceAtomicWriter = { async run(operation) { return operation({ transaction: { afterCommit() {} }, async stage(mutation) { return { ok: true, value: mutation }; } }); } };
compatibleWriter.run(() => ({ ok: true, value: 1 }), {});
persistenceCommandDiagnosticRecord({ operation: "write_atomic", boundary: "invocation", role: "primary", condition: "transaction-canceled", codeStatus: "recognized", effect: "unknown" });
// @ts-expect-error native command messages are not diagnostic data.
persistenceCommandDiagnosticRecord({ operation: "write_atomic", boundary: "invocation", role: "primary", condition: "transaction-canceled", codeStatus: "recognized", effect: "unknown", message: "private" });
// @ts-expect-error attribute observations explicitly state truncation.
persistenceStoredAttributeDiagnosticRecord({ operation: "read_outbox", reduction: "thrown", effect: "not-assessed", issues: [{ field: "state", condition: "closed-value-rejected" }] });
// @ts-expect-error successful reconciliation validation does not confirm a write.
persistenceStateReconciliationDiagnosticRecord({ operation: "complete_processing", primaryOutcome: "condition-rejected", observed: "valid-current-state", effect: "write-confirmed" });
persistenceRelayBoundaryDiagnosticRecord({ operation: "run-once", boundary: "publish-marker", reason: "returned-failure", effect: "send-success-marker-outcome-unknown" });
// @ts-expect-error a failed send does not establish nonacceptance.
persistenceRelayBoundaryDiagnosticRecord({ operation: "run-once", boundary: "queue-send", reason: "returned-failure", effect: "not-accepted" });

function accepted<TValue, TError>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false; readonly error: TError }): TValue {
  if (!result.ok) {
    throw new Error("Expected valid test fixture value.");
  }

  return result.value;
}
