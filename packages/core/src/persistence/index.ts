import {
  brand,
  err,
  messageKey,
  ok,
  type Brand,
  type CoreError,
  type MessageKey,
  type MessageParams,
  type Result,
} from "../shared/index";

export type ConcurrencyToken = Brand<string, "ConcurrencyToken">;
export type PageTotal = Brand<number, "PageTotal">;

export type PersistenceErrorCode =
  | "PERSISTENCE_CONFLICT"
  | "PERSISTENCE_DUPLICATE"
  | "PERSISTENCE_INVALID_PAGE"
  | "PERSISTENCE_INVALID_PAGE_REQUEST"
  | "PERSISTENCE_NOT_FOUND"
  | "PERSISTENCE_TIMEOUT"
  | "PERSISTENCE_TRANSACTION_FAILED"
  | "PERSISTENCE_UNAVAILABLE";

export interface PersistenceError extends CoreError {
  readonly code: PersistenceErrorCode;
}

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

export interface SaveOptions {
  readonly expectedConcurrencyToken?: ConcurrencyToken;
}

export interface Transaction {
  afterCommit(action: () => Promise<void> | void): void;
}

export interface Repository<TEntity, TId> {
  get(id: TId): Promise<TEntity | null>;
  save(entity: TEntity, options?: SaveOptions): Promise<Result<TEntity, PersistenceError>>;
}

export interface UnitOfWork {
  run<TValue>(operation: (transaction: Transaction) => Promise<TValue> | TValue): Promise<TValue>;
}

export interface InMemoryRepositoryOptions<TEntity, TId> {
  readonly getId: (entity: TEntity) => TId;
  readonly getConcurrencyToken?: (entity: TEntity) => ConcurrencyToken | undefined;
  readonly clone?: (entity: TEntity) => TEntity;
  readonly initialEntities?: readonly TEntity[];
}

export function concurrencyToken(value: string): ConcurrencyToken {
  return brand<string, "ConcurrencyToken">(value);
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
  const totalItems =
    rawTotalItems === undefined ? undefined : pageTotal(rawTotalItems);
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

export function persistenceError(input: {
  readonly code: PersistenceErrorCode;
  readonly defaultMessage: string;
  readonly messageKey?: string | MessageKey;
  readonly params?: MessageParams;
  readonly cause?: unknown;
  readonly details?: Readonly<Record<string, unknown>>;
}): PersistenceError {
  return {
    code: input.code,
    defaultMessage: input.defaultMessage,
    ...(input.messageKey === undefined ? {} : { messageKey: messageKey(input.messageKey) }),
    ...(input.params === undefined ? {} : { params: input.params }),
    ...(input.cause === undefined ? {} : { cause: input.cause }),
    ...(input.details === undefined ? {} : { details: input.details }),
  };
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

export function inMemoryRepository<TEntity, TId>(
  options: InMemoryRepositoryOptions<TEntity, TId>,
): Repository<TEntity, TId> {
  const records = new Map<TId, TEntity>();
  const cloneEntity = (entity: TEntity): TEntity => clone(entity, options.clone);

  for (const entity of options.initialEntities ?? []) {
    records.set(options.getId(entity), cloneEntity(entity));
  }

  return {
    async get(id) {
      const entity = records.get(id);
      return entity === undefined ? null : cloneEntity(entity);
    },

    async save(entity, saveOptions = {}) {
      const id = options.getId(entity);

      if (saveOptions.expectedConcurrencyToken !== undefined) {
        const current = records.get(id);
        const currentToken = current === undefined ? undefined : options.getConcurrencyToken?.(current);

        if (currentToken !== saveOptions.expectedConcurrencyToken) {
          return err(
            persistenceError({
              code: "PERSISTENCE_CONFLICT",
              defaultMessage: "The stored entity changed before it could be saved.",
              messageKey: "persistence.conflict",
              params: { id: String(id) },
            }),
          );
        }
      }

      const stored = cloneEntity(entity);
      records.set(id, stored);
      return ok(cloneEntity(stored));
    },
  };
}

export function inMemoryUnitOfWork(): UnitOfWork {
  return {
    async run(operation) {
      const afterCommitActions: Array<() => Promise<void> | void> = [];
      let open = true;
      const transaction: Transaction = {
        afterCommit(action) {
          if (!open) {
            throw new TypeError("Cannot register after-commit actions after the transaction is closed.");
          }
          afterCommitActions.push(action);
        },
      };

      try {
        const value = await operation(transaction);
        open = false;

        for (const action of afterCommitActions) {
          await action();
        }

        return value;
      } catch (error) {
        open = false;
        throw error;
      }
    },
  };
}

function clone<TEntity>(entity: TEntity, cloneEntity?: (entity: TEntity) => TEntity): TEntity {
  if (cloneEntity !== undefined) {
    return cloneEntity(entity);
  }

  if (Array.isArray(entity)) {
    return [...entity] as TEntity;
  }

  if (entity !== null && typeof entity === "object") {
    return { ...entity };
  }

  return entity;
}

function invalidPageTotalError(field: string, value: number): PersistenceError {
  return persistenceError({
    code: "PERSISTENCE_INVALID_PAGE",
    defaultMessage: "Page total must be a non-negative integer.",
    messageKey: "persistence.page.invalid_total",
    params: { field, total: String(value) },
  });
}
