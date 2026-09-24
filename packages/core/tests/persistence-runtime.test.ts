import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import {
  concurrencyToken,
  inMemoryRepository,
  inMemoryUnitOfWork,
  isRecordLifecycleActive,
  logicallyDeleteRecord,
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  outboxMessageVersion,
  page,
  pageRequest,
  pageTotal,
  pageTotals,
  persistenceError,
  recordChange,
  recordChangeFieldName,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
  recordLifecyclePolicy,
  recordPurgeEligibility,
  recordRetentionPolicyReference,
  restoreLogicallyDeletedRecord,
  activeRecordLifecycle,
  type ConcurrencyToken,
  type Transaction,
} from "../src/persistence/index";
import { diagnosticDescriptor } from "../src/diagnostics/index";
import { causationId, entityId, isErr, isOk, isoDateTimeFromDate, type EntityId } from "../src/shared/index";

type DealId = EntityId<"DealId">;

interface DealRecord {
  readonly id: DealId;
  readonly name: string;
  readonly concurrencyToken: ConcurrencyToken;
  readonly tags: string[];
}

const dealId = entityId<"DealId">("deal-123");
const firstVersion = concurrencyToken("deal-123:v1");
const secondVersion = concurrencyToken("deal-123:v2");
const thirdVersion = concurrencyToken("deal-123:v3");

async function main(): Promise<void> {
  const validPageRequest = pageRequest({ limit: 25, cursor: "cursor-1" });
  equal(isOk(validPageRequest), true);
  if (!isOk(validPageRequest)) {
    throw new Error("Expected valid page request.");
  }
  deepEqual(validPageRequest.value, { limit: 25, cursor: "cursor-1" });

  const invalidLimit = pageRequest({ limit: 0 });
  equal(isErr(invalidLimit), true);
  if (!isErr(invalidLimit)) {
    throw new Error("Expected invalid page request.");
  }
  equal(invalidLimit.error.code, "PERSISTENCE_INVALID_PAGE_REQUEST");
  equal(invalidLimit.error.messageKey, "persistence.page_request.invalid_limit");

  const invalidCursor = pageRequest({ limit: 10, cursor: "" });
  equal(isErr(invalidCursor), true);
  if (!isErr(invalidCursor)) {
    throw new Error("Expected invalid cursor.");
  }
  equal(invalidCursor.error.code, "PERSISTENCE_INVALID_PAGE_REQUEST");
  equal(invalidCursor.error.messageKey, "persistence.page_request.invalid_cursor");

  const firstPage = page({ items: ["deal-1", "deal-2"], nextCursor: "cursor-2" });
  deepEqual(firstPage, { items: ["deal-1", "deal-2"], nextCursor: "cursor-2" });

  const totalItems = pageTotal(100);
  equal(isOk(totalItems), true);
  if (!isOk(totalItems)) {
    throw new Error("Expected page total to be valid.");
  }
  equal(totalItems.value, 100);

  const invalidTotal = pageTotal(-1);
  equal(isErr(invalidTotal), true);
  if (!isErr(invalidTotal)) {
    throw new Error("Expected negative page total to fail.");
  }
  equal(invalidTotal.error.code, "PERSISTENCE_INVALID_PAGE");

  const totals = pageTotals({ totalItems: 100, totalMatchingItems: 12 });
  equal(isOk(totals), true);
  if (!isOk(totals)) {
    throw new Error("Expected page totals to be valid.");
  }
  deepEqual(totals.value, { totalItems: 100, totalMatchingItems: 12 });

  const invalidTotals = pageTotals({ totalItems: 10, totalMatchingItems: 11 });
  equal(isErr(invalidTotals), true);
  if (!isErr(invalidTotals)) {
    throw new Error("Expected invalid page totals to fail.");
  }
  equal(invalidTotals.error.messageKey, "persistence.page.invalid_total_relationship");

  const pageWithTotals = page({ items: ["deal-1"], totals: totals.value });
  deepEqual(pageWithTotals, {
    items: ["deal-1"],
    totals: { totalItems: 100, totalMatchingItems: 12 },
  });

  const items = ["deal-1"];
  const copiedPage = page({ items });
  items.push("deal-2");
  deepEqual(copiedPage.items, ["deal-1"]);

  const explicitError = persistenceError({
    code: "PERSISTENCE_TIMEOUT",
    defaultMessage: "Storage operation timed out.",
    messageKey: "persistence.timeout",
    diagnostic: diagnosticDescriptor({
      failureKind: "timeout",
      failureSource: "provider",
      severity: "error",
      recovery: "automation_retryable",
      action: "retry",
    }),
  });
  equal(explicitError.code, "PERSISTENCE_TIMEOUT");
  equal(explicitError.messageKey, "persistence.timeout");
  equal(explicitError.diagnostic?.retryable, true);

  const recordedAt = isoDateTimeFromDate(new Date("2026-09-23T12:00:00.000Z"));
  const retentionReference = recordRetentionPolicyReference("platform-smoke.work-item-retention.v1");
  equal(isOk(retentionReference), true);
  if (!isOk(retentionReference)) {
    throw new Error("Expected a valid logical-record retention reference.");
  }
  const lifecyclePolicy = recordLifecyclePolicy({
    recoveryWindowMs: 60_000,
    retentionPolicy: retentionReference.value,
    legalHoldCheckRequired: true,
  });
  equal(isOk(lifecyclePolicy), true);
  if (!isOk(lifecyclePolicy)) {
    throw new Error("Expected a valid logical-record lifecycle policy.");
  }
  const deletedLifecycle = logicallyDeleteRecord({
    current: activeRecordLifecycle(),
    deletedAt: recordedAt,
    policy: lifecyclePolicy.value,
  });
  equal(isOk(deletedLifecycle), true);
  if (!isOk(deletedLifecycle)) {
    throw new Error("Expected logical deletion to succeed for an active record.");
  }
  equal(isRecordLifecycleActive(deletedLifecycle.value), false);
  equal(deletedLifecycle.value.state, "deleted");
  if (deletedLifecycle.value.state !== "deleted") {
    throw new Error("Expected logical deletion to retain deletion facts.");
  }
  equal(deletedLifecycle.value.retentionPolicy, retentionReference.value);
  const repeatedDeletion = logicallyDeleteRecord({
    current: deletedLifecycle.value,
    deletedAt: recordedAt,
    policy: lifecyclePolicy.value,
  });
  equal(isErr(repeatedDeletion), true);
  if (!isErr(repeatedDeletion)) {
    throw new Error("Expected repeated logical deletion to fail.");
  }
  equal(repeatedDeletion.error.code, "PERSISTENCE_INVALID_RECORD_LIFECYCLE");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:00:30.000Z")),
    retentionSatisfied: true,
    legalHold: false,
  }), "within-recovery-window");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
    retentionSatisfied: true,
    legalHold: true,
  }), "legal-hold");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
    retentionSatisfied: false,
    legalHold: false,
  }), "retention-not-met");
  equal(recordPurgeEligibility({
    current: deletedLifecycle.value,
    asOf: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
    retentionSatisfied: true,
    legalHold: false,
  }), "eligible");
  const restoredLifecycle = restoreLogicallyDeletedRecord({
    current: deletedLifecycle.value,
    restoredAt: isoDateTimeFromDate(new Date("2026-09-23T12:00:59.000Z")),
  });
  equal(isOk(restoredLifecycle), true);
  if (!isOk(restoredLifecycle)) {
    throw new Error("Expected restoration inside the recovery window to succeed.");
  }
  equal(isRecordLifecycleActive(restoredLifecycle.value), true);
  const expiredRestore = restoreLogicallyDeletedRecord({
    current: deletedLifecycle.value,
    restoredAt: isoDateTimeFromDate(new Date("2026-09-23T12:01:01.000Z")),
  });
  equal(isErr(expiredRestore), true);
  if (!isErr(expiredRestore)) {
    throw new Error("Expected restoration after the recovery window to fail.");
  }
  equal(expiredRestore.error.code, "PERSISTENCE_RESTORE_WINDOW_EXPIRED");
  const restoreActive = restoreLogicallyDeletedRecord({
    current: activeRecordLifecycle(),
    restoredAt: recordedAt,
  });
  equal(isErr(restoreActive), true);
  if (!isErr(restoreActive)) {
    throw new Error("Expected restoration of an active record to fail.");
  }
  equal(restoreActive.error.code, "PERSISTENCE_RECORD_NOT_DELETED");
  equal(recordPurgeEligibility({
    current: activeRecordLifecycle(),
    asOf: recordedAt,
    retentionSatisfied: true,
    legalHold: false,
  }), "not-deleted");
  const messageType = outboxMessageType("platform-smoke.work.accepted");
  const deliveryPolicy = outboxDeliveryPolicy("platform-short-idempotent-work.v1");
  const messageVersion = outboxMessageVersion(2);
  const lineageKind = recordKind("platform-smoke.work-item");
  const lineageId = recordId("work-1");
  const lineageRevision = recordRevision(1);
  const stateField = recordChangeFieldName("state");
  equal(isOk(messageType), true);
  equal(isOk(deliveryPolicy), true);
  equal(isOk(messageVersion), true);
  if (!isOk(messageType) || !isOk(deliveryPolicy) || !isOk(messageVersion) || !isOk(lineageKind) || !isOk(lineageId) || !isOk(lineageRevision) || !isOk(stateField)) {
    throw new Error("Expected valid durable-delivery facts.");
  }
  const durableEntry = outboxEntry({
    id: outboxEntryId("outbox-1"),
    subject: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    messageType: messageType.value,
    messageVersion: messageVersion.value,
    deliveryPolicy: deliveryPolicy.value,
    createdAt: recordedAt,
    causationId: causationId("request-1"),
  });
  equal(durableEntry.messageVersion, 2);
  equal(durableEntry.messageType, "platform-smoke.work.accepted");
  equal(isErr(outboxMessageType("Platform Smoke")), true);
  equal(isErr(outboxDeliveryPolicy("no-space policy")), true);
  equal(isErr(outboxMessageVersion(0)), true);

  const lineage = recordChange({
    id: recordChangeId("change-1"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "updated",
    occurredAt: recordedAt,
    causationId: causationId("request-1"),
    changedFields: [stateField.value],
  });
  equal(isOk(lineage), true);
  if (!isOk(lineage)) {
    throw new Error("Expected valid record change.");
  }
  deepEqual(lineage.value.changedFields, ["state"]);
  const duplicateFields = recordChange({
    id: recordChangeId("change-2"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "updated",
    occurredAt: recordedAt,
    changedFields: [stateField.value, stateField.value],
  });
  equal(isErr(duplicateFields), true);
  if (!isErr(duplicateFields)) {
    throw new Error("Expected duplicate lineage fields to fail.");
  }
  equal(duplicateFields.error.code, "PERSISTENCE_INVALID_LINEAGE");
  const deletedLineage = recordChange({
    id: recordChangeId("change-3"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "deleted",
    occurredAt: recordedAt,
    changedFields: [stateField.value],
  });
  const restoredLineage = recordChange({
    id: recordChangeId("change-4"),
    record: recordReference({ kind: lineageKind.value, id: lineageId.value }),
    revision: lineageRevision.value,
    action: "restored",
    occurredAt: recordedAt,
    changedFields: [stateField.value],
  });
  equal(isOk(deletedLineage), true);
  equal(isOk(restoredLineage), true);
  if (!isOk(deletedLineage) || !isOk(restoredLineage)) {
    throw new Error("Expected deletion and restoration to use the bounded lineage vocabulary.");
  }
  equal(deletedLineage.value.action, "deleted");
  equal(restoredLineage.value.action, "restored");

  const repository = inMemoryRepository<DealRecord, DealId>({
    getId: (deal) => deal.id,
    getConcurrencyToken: (deal) => deal.concurrencyToken,
    clone: (deal) => ({ ...deal, tags: [...deal.tags] }),
    initialEntities: [
      {
        id: dealId,
        name: "Initial deal",
        concurrencyToken: firstVersion,
        tags: ["seed"],
      },
    ],
  });

  const loaded = await repository.get(dealId);
  if (loaded === null) {
    throw new Error("Expected seeded deal.");
  }
  deepEqual(loaded, {
    id: "deal-123",
    name: "Initial deal",
    concurrencyToken: "deal-123:v1",
    tags: ["seed"],
  });

  loaded.tags.push("mutated");
  const reloaded = await repository.get(dealId);
  deepEqual(reloaded?.tags, ["seed"]);

  const saved = await repository.save(
    {
      id: dealId,
      name: "Updated deal",
      concurrencyToken: secondVersion,
      tags: ["updated"],
    },
    { expectedConcurrencyToken: firstVersion },
  );
  equal(isOk(saved), true);
  if (!isOk(saved)) {
    throw new Error("Expected save to succeed.");
  }
  equal(saved.value.name, "Updated deal");

  const staleSave = await repository.save(
    {
      id: dealId,
      name: "Stale update",
      concurrencyToken: thirdVersion,
      tags: ["stale"],
    },
    { expectedConcurrencyToken: firstVersion },
  );
  equal(isErr(staleSave), true);
  if (!isErr(staleSave)) {
    throw new Error("Expected stale save to fail.");
  }
  equal(staleSave.error.code, "PERSISTENCE_CONFLICT");

  const missing = await repository.get(entityId<"DealId">("missing-deal"));
  equal(missing, null);

  const unitOfWork = inMemoryUnitOfWork();
  const unsupportedTransactionalSave = await unitOfWork.run((transaction) =>
    repository.save(
      {
        id: dealId,
        name: "Transaction attempt",
        concurrencyToken: thirdVersion,
        tags: ["transaction"],
      },
      { transaction },
    ),
  );
  equal(isErr(unsupportedTransactionalSave), true);
  if (!isErr(unsupportedTransactionalSave)) {
    throw new Error("Expected in-memory repository to reject a transaction handle.");
  }
  equal(unsupportedTransactionalSave.error.code, "PERSISTENCE_TRANSACTION_UNSUPPORTED");

  const events: string[] = [];
  const value = await unitOfWork.run((transaction) => {
    transaction.afterCommit(() => {
      events.push("first-after-commit");
    });
    transaction.afterCommit(async () => {
      events.push("second-after-commit");
    });
    events.push("inside-transaction");
    return "done";
  });
  equal(value, "done");
  deepEqual(events, ["inside-transaction", "first-after-commit", "second-after-commit"]);

  const rolledBackEvents: string[] = [];
  await rejects(
    unitOfWork.run(async (transaction) => {
      transaction.afterCommit(() => {
        rolledBackEvents.push("should-not-run");
      });
      throw new Error("operation failed");
    }),
    (error: unknown) =>
      isPersistenceTransactionError(error) &&
      error.cause instanceof Error &&
      error.cause.message === "operation failed",
  );
  deepEqual(rolledBackEvents, []);

  let capturedTransaction: Transaction | undefined;
  await unitOfWork.run((transaction) => {
    capturedTransaction = transaction;
  });
  if (capturedTransaction === undefined) {
    throw new Error("Expected transaction to be captured.");
  }
  const closedTransaction = capturedTransaction;
  throws(() => closedTransaction.afterCommit(() => undefined), /transaction is closed/);
}

function isPersistenceTransactionError(error: unknown): error is {
  readonly code: "PERSISTENCE_TRANSACTION_FAILED";
  readonly cause?: unknown;
} {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    error.code === "PERSISTENCE_TRANSACTION_FAILED"
  );
}

main()
  .then(() => {
    console.log("packages/core persistence runtime test passed.");
  })
  .catch((error: unknown) => {
    console.error(error);
    process.exitCode = 1;
  });
