import { brand, err, ok, type Brand, type Result } from "../shared/index";
import { persistenceError, type PersistenceError } from "./errors";

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
  if (!Number.isInteger(value) || value < 0) {
    return err(invalidPageTotalError("total", value));
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
    return err(invalidPageTotalError("totalItems", rawTotalItems!));
  }

  const totalMatchingItems =
    rawTotalMatchingItems === undefined ? undefined : pageTotal(rawTotalMatchingItems);
  if (totalMatchingItems !== undefined && !totalMatchingItems.ok) {
    return err(invalidPageTotalError("totalMatchingItems", rawTotalMatchingItems!));
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
  if (!Number.isInteger(input.limit) || input.limit <= 0) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_PAGE_REQUEST",
        defaultMessage: "Page limit must be a positive integer.",
        messageKey: "persistence.page_request.invalid_limit",
        params: { limit: String(input.limit) },
      }),
    );
  }

  if (input.cursor !== undefined && input.cursor.length === 0) {
    return err(
      persistenceError({
        code: "PERSISTENCE_INVALID_PAGE_REQUEST",
        defaultMessage: "Page cursor must not be empty.",
        messageKey: "persistence.page_request.invalid_cursor",
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

function invalidPageTotalError(field: string, value: number): PersistenceError {
  return persistenceError({
    code: "PERSISTENCE_INVALID_PAGE",
    defaultMessage: "Page total must be a non-negative integer.",
    messageKey: "persistence.page.invalid_total",
    params: { field, total: String(value) },
  });
}
