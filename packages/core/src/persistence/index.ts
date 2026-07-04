import type { Result } from "../shared/index";

export interface PageRequest {
  readonly limit: number;
  readonly cursor?: string;
}

export interface Page<TItem> {
  readonly items: readonly TItem[];
  readonly nextCursor?: string;
}

export interface Transaction {
  afterCommit(action: () => Promise<void> | void): void;
}

export interface Repository<TEntity, TId> {
  get(id: TId): Promise<TEntity | null>;
  save(entity: TEntity): Promise<Result<TEntity>>;
}

export interface UnitOfWork {
  run<TValue>(operation: (transaction: Transaction) => Promise<TValue>): Promise<TValue>;
}
