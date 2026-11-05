import { brand, err, ok, type Brand, type Result } from "../shared/index";
import { persistenceError, type PersistenceError } from "./errors";
import { corePersistenceValidationRecord, type CorePersistenceValidationDetail } from "./diagnostics";

export type PageTotal = Brand<number, "PageTotal">;

export interface PageRequest {
  readonly limit: number;
  readonly cursor?: string;
}

export interface Page<TItem> {
  readonly items: readonly TItem[];
  readonly nextCursor?: string;
  readonly totals?: PageTotals;
}

export interface PageTotals {
  readonly totalItems?: PageTotal;
  readonly totalMatchingItems?: PageTotal;
}

export function pageTotal(value: number): Result<PageTotal, PersistenceError> {
  const integer = Number.isInteger(value);
  if (!integer || value < 0) {
    return err(invalidPageTotalError("total", value, "page-total", integer ? "negative" : "not-integer"));
  }

  return ok(brand<number, "PageTotal">(value));
}

export function pageTotals(input: {
  readonly totalItems?: number;
  readonly totalMatchingItems?: number;
}): Result<PageTotals, PersistenceError> {
  const rawTotalItems = input.totalItems;
  const rawTotalMatchingItems = input.totalMatchingItems;
  const totalItems = rawTotalItems === undefined ? undefined : pageTotal(rawTotalItems);
  if (totalItems !== undefined && !totalItems.ok) {
    const reason = (totalItems.error.diagnosticRecord!.detail as CorePersistenceValidationDetail).reason;
    return err(invalidPageTotalError("totalItems", rawTotalItems!, "page-totals", reason));
  }

  const totalMatchingItems =
    rawTotalMatchingItems === undefined ? undefined : pageTotal(rawTotalMatchingItems);
  if (totalMatchingItems !== undefined && !totalMatchingItems.ok) {
    const reason = (totalMatchingItems.error.diagnosticRecord!.detail as CorePersistenceValidationDetail).reason;
    return err(invalidPageTotalError("totalMatchingItems", rawTotalMatchingItems!, "page-totals", reason));
  }

  if (
    totalItems !== undefined &&
    totalMatchingItems !== undefined &&
    totalMatchingItems.value > totalItems.value
  ) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_PAGE",
        defaultMessage: "Matching page total must not exceed overall page total.",
        messageKey: "persistence.page.invalid_total_relationship",
        diagnosticRecord: corePersistenceValidationRecord({ operation: "page-totals", field: "totals", reason: "matching-exceeds-total" }),
        params: {
          totalItems: String(totalItems.value),
          totalMatchingItems: String(totalMatchingItems.value),
        },
      }),
    );
  }

  return ok({
    ...(totalItems === undefined ? {} : { totalItems: totalItems.value }),
    ...(totalMatchingItems === undefined ? {} : { totalMatchingItems: totalMatchingItems.value }),
  });
}

export function pageRequest(input: {
  readonly limit: number;
  readonly cursor?: string;
}): Result<PageRequest, PersistenceError> {
  const integerLimit = Number.isInteger(input.limit);
  if (!integerLimit || input.limit <= 0) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_PAGE_REQUEST",
        defaultMessage: "Page limit must be a positive integer.",
        messageKey: "persistence.page_request.invalid_limit",
        params: { limit: String(input.limit) },
        diagnosticRecord: corePersistenceValidationRecord({ operation: "page-request", field: "limit", reason: integerLimit ? "not-positive" : "not-integer" }),
      }),
    );
  }

  if (input.cursor !== undefined && input.cursor.length === 0) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_PAGE_REQUEST",
        defaultMessage: "Page cursor must not be empty.",
        messageKey: "persistence.page_request.invalid_cursor",
        diagnosticRecord: corePersistenceValidationRecord({ operation: "page-request", field: "cursor", reason: "empty" }),
      }),
    );
  }

  return ok({
    limit: input.limit,
    ...(input.cursor === undefined ? {} : { cursor: input.cursor }),
  });
}

export function page<TItem>(input: {
  readonly items: readonly TItem[];
  readonly nextCursor?: string;
  readonly totals?: PageTotals;
}): Page<TItem> {
  return {
    items: [...input.items],
    ...(input.nextCursor === undefined ? {} : { nextCursor: input.nextCursor }),
    ...(input.totals === undefined ? {} : { totals: { ...input.totals } }),
  };
}

function invalidPageTotalError(field: "total" | "totalItems" | "totalMatchingItems", value: number, operation: "page-total" | "page-totals", reason: CorePersistenceValidationDetail["reason"]): PersistenceError {
  return persistenceError({
    code: "PERSISTENCE_INVALID_PAGE",
    defaultMessage: "Page total must be a non-negative integer.",
    messageKey: "persistence.page.invalid_total",
    params: { field, total: String(value) },
    diagnosticRecord: corePersistenceValidationRecord({ operation, field, reason }),
  });
}
