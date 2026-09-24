export interface Transaction {
  afterCommit(action: () => Promise<void> | void): void;
}

export interface UnitOfWork {
  run<TValue>(operation: (transaction: Transaction) => Promise<TValue> | TValue): Promise<TValue>;
}
