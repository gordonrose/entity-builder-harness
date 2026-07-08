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
  type Page,
  type PageRequest,
  type PageTotal,
  type PageTotals,
  type PersistenceError,
  type PersistenceErrorCode,
  type Repository,
  type SaveOptions,
  type Transaction,
  type UnitOfWork,
} from "../src/persistence/index";
import { entityId, isOk, type EntityId, type Result } from "../src/shared/index";

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
