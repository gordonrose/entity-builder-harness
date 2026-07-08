import { deepEqual, equal, rejects, throws } from "node:assert/strict";
import {
  concurrencyToken,
  inMemoryRepository,
  inMemoryUnitOfWork,
  page,
  pageRequest,
  pageTotal,
  pageTotals,
  persistenceError,
  type ConcurrencyToken,
  type Transaction,
} from "../src/persistence/index";
import { diagnosticDescriptor } from "../src/diagnostics/index";
import { entityId, isErr, isOk, type EntityId } from "../src/shared/index";

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
