import type { Result } from "../shared/index";
import type { ConcurrencyToken } from "./concurrency";
import type { PersistenceError } from "./errors";
import type { Transaction } from "./transactions";

export interface SaveOptions {
  readonly expectedConcurrencyToken?: ConcurrencyToken;
  /**
   * The transaction supplied by a provider-specific unit of work. Repositories
   * that cannot enlist in it must reject the save rather than silently writing
   * outside the requested atomic boundary.
   */
  readonly transaction?: Transaction;
}

export interface Repository<TEntity, TId> {
  get(id: TId): Promise<TEntity | null>;
  save(entity: TEntity, options?: SaveOptions): Promise<Result<TEntity, PersistenceError>>;
}
