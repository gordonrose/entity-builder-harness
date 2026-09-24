import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import {
  concurrencyToken,
  inMemoryRepository,
  inMemoryUnitOfWork,
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
