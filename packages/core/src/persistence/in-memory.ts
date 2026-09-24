import { err, ok } from "../shared/index";
import type { ConcurrencyToken } from "./concurrency";
import { persistenceError } from "./errors";
import type { Repository } from "./repository";
import type { Transaction, UnitOfWork } from "./transactions";

export interface InMemoryRepositoryOptions<TEntity, TId> {
  readonly getId: (entity: TEntity) => TId;
  readonly getConcurrencyToken?: (entity: TEntity) => ConcurrencyToken | undefined;
  readonly clone?: (entity: TEntity) => TEntity;
  readonly initialEntities?: readonly TEntity[];
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
      if (saveOptions.transaction !== undefined) {
        return err(
          persistenceError({
            code: "PERSISTENCE_TRANSACTION_UNSUPPORTED",
            defaultMessage: "The in-memory repository cannot participate in a durable transaction.",
            messageKey: "persistence.transaction.unsupported",
          }),
        );
      }

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
        throw persistenceError({
          code: "PERSISTENCE_TRANSACTION_FAILED",
          defaultMessage: "Transaction failed before it could complete.",
          messageKey: "persistence.transaction.failed",
          cause: error,
        });
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
