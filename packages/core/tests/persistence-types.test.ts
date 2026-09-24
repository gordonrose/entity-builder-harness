import {
  concurrencyToken,
  inMemoryRepository,
  inMemoryUnitOfWork,
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  page,
  pageRequest,
  pageTotal,
  pageTotals,
  persistenceError,
  recordChange,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
  type ConcurrencyToken,
  type Page,
  type PageRequest,
  type PageTotal,
  type PageTotals,
  type OutboxEntry,
  type PersistenceError,
  type PersistenceErrorCode,
  type Repository,
  type RecordChange,
  type SaveOptions,
  type Transaction,
  type UnitOfWork,
} from "../src/persistence/index";
import { entityId, isOk, isoDateTimeFromDate, type EntityId, type Result } from "../src/shared/index";

type DealId = EntityId<"DealId">;

interface DealRecord {
  readonly id: DealId;
  readonly name: string;
  readonly concurrencyToken: ConcurrencyToken;
}

const dealId = entityId<"DealId">("deal-123");
const version = concurrencyToken("deal-123:v1");
const acceptedCode: PersistenceErrorCode = "PERSISTENCE_CONFLICT";
const acceptedError: PersistenceError = persistenceError({
  code: acceptedCode,
  defaultMessage: "The stored entity changed before it could be saved.",
  messageKey: "persistence.conflict",
});
const requestResult: Result<PageRequest, PersistenceError> = pageRequest({ limit: 25 });
const totalResult: Result<PageTotal, PersistenceError> = pageTotal(100);
const totalsResult: Result<PageTotals, PersistenceError> = pageTotals({
  totalItems: 100,
  totalMatchingItems: 12,
});
const saveOptions: SaveOptions = { expectedConcurrencyToken: version };
const firstPage: Page<DealRecord> = page({
  items: [{ id: dealId, name: "Deal", concurrencyToken: version }],
});
const pageWithTotals: Page<DealRecord> = isOk(totalsResult)
  ? page({
      items: [{ id: dealId, name: "Deal", concurrencyToken: version }],
      totals: totalsResult.value,
    })
  : page({ items: [] });
const repository: Repository<DealRecord, DealId> = inMemoryRepository({
  getId: (deal) => deal.id,
  getConcurrencyToken: (deal) => deal.concurrencyToken,
});
const unitOfWork: UnitOfWork = inMemoryUnitOfWork();
const recordedAt = isoDateTimeFromDate(new Date("2026-09-23T12:00:00.000Z"));
const messageTypeResult = outboxMessageType("platform-smoke.work.accepted");
const deliveryPolicyResult = outboxDeliveryPolicy("platform-short-idempotent-work.v1");
const lineageKindResult = recordKind("platform-smoke.work-item");
const lineageIdResult = recordId("work-1");
const lineageRevisionResult = recordRevision(1);

if (!isOk(messageTypeResult) || !isOk(deliveryPolicyResult) || !isOk(lineageKindResult) || !isOk(lineageIdResult) || !isOk(lineageRevisionResult)) {
  throw new Error("Expected valid durable-delivery fixtures.");
}

const durableEntry: OutboxEntry = outboxEntry({
  id: outboxEntryId("outbox-1"),
  subject: recordReference({ kind: lineageKindResult.value, id: lineageIdResult.value }),
  messageType: messageTypeResult.value,
  deliveryPolicy: deliveryPolicyResult.value,
  createdAt: recordedAt,
});
const lineage: Result<RecordChange, PersistenceError> = recordChange({
  id: recordChangeId("change-1"),
  record: recordReference({ kind: lineageKindResult.value, id: lineageIdResult.value }),
  revision: lineageRevisionResult.value,
  action: "created",
  occurredAt: recordedAt,
});

if (isOk(requestResult)) {
  const pageSize: number = requestResult.value.limit;
  void pageSize;
}

void acceptedError;
void totalResult;
void saveOptions;
void firstPage;
void pageWithTotals;
void repository;
void unitOfWork;
void durableEntry;
void lineage;

unitOfWork.run((transaction: Transaction) => {
  transaction.afterCommit(() => undefined);
  return "ok";
});

repository.get(dealId);
repository.save({ id: dealId, name: "Deal", concurrencyToken: version }, saveOptions);

// @ts-expect-error concurrency tokens must be explicitly branded.
const invalidToken: ConcurrencyToken = "deal-123:v1";
void invalidToken;

// @ts-expect-error persistence error codes are constrained.
persistenceError({ code: "DATABASE_LOCKED", defaultMessage: "Database locked." });

// @ts-expect-error page request limit is required.
pageRequest({ cursor: "cursor-1" });

// @ts-expect-error page totals must use branded PageTotal values.
const invalidPageTotals: PageTotals = { totalItems: 100 };
void invalidPageTotals;

// @ts-expect-error repository get requires the branded entity id.
repository.get("deal-123");

// @ts-expect-error save expected concurrency token must be branded.
repository.save({ id: dealId, name: "Deal", concurrencyToken: version }, { expectedConcurrencyToken: "deal-123:v1" });

// @ts-expect-error repository save failures must use persistence errors.
const invalidSave: Repository<DealRecord, DealId>["save"] = async () => ({
  ok: false,
  error: { code: "DATABASE_LOCKED", defaultMessage: "Database locked." },
});
void invalidSave;

// @ts-expect-error outbox entries intentionally carry routing facts rather than a raw payload.
const invalidOutboxEntry: OutboxEntry = { ...durableEntry, payload: { email: "private@example.test" } };
void invalidOutboxEntry;

if (isOk(lineage)) {
  // @ts-expect-error record changes intentionally exclude unrestricted historical metadata.
  const invalidLineage: RecordChange = { ...lineage.value, metadata: { before: "private" } };
  void invalidLineage;
}
