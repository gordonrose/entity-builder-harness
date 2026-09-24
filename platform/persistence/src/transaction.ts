import type {
  OutboxEntry,
  RecordChange,
  Transaction,
} from "@kanbien/core/persistence";
import { err, ok, type Result } from "@kanbien/core/shared";
import { platformPersistenceError, type PlatformPersistenceError } from "./errors";

/**
 * The safe facts that must be written with a product's state change.
 * The product repository performs its write with the transaction supplied by
 * the scope; an adapter makes all three writes atomic in its chosen store.
 */
export interface PlatformPersistenceMutation {
  readonly recordChange: RecordChange;
  readonly outboxEntry: OutboxEntry;
}

/**
 * A scope is valid only for one call to an atomic writer. Consumers pass its
 * transaction to a repository that explicitly supports transactions, then
 * stage one or more validated durable-delivery mutations through this scope.
 */
export interface PlatformPersistenceTransactionScope {
  readonly transaction: Transaction;
  stage(
    mutation: PlatformPersistenceMutation,
  ): Promise<Result<PlatformPersistenceMutation, PlatformPersistenceError>>;
}

/**
 * Provider adapters implement this port. A failed operation or failed stage
 * must roll back the state write, lineage record, and outbox entry together.
 */
export interface PlatformPersistenceAtomicWriter {
  run<TValue, TFailure>(
    operation: (
      scope: PlatformPersistenceTransactionScope,
    ) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>,
  ): Promise<Result<TValue, TFailure | PlatformPersistenceError>>;
}

export function platformPersistenceMutation(input: {
  readonly recordChange: RecordChange;
  readonly outboxEntry: OutboxEntry;
}): Result<PlatformPersistenceMutation, PlatformPersistenceError> {
  if (
    input.recordChange.record.kind !== input.outboxEntry.subject.kind ||
    input.recordChange.record.id !== input.outboxEntry.subject.id
  ) {
    return invalidMutation("The outbox subject must match the record-change subject.", "subject_mismatch");
  }

  if (
    input.recordChange.causationId === undefined ||
    input.outboxEntry.causationId === undefined ||
    input.recordChange.causationId !== input.outboxEntry.causationId
  ) {
    return invalidMutation("The outbox entry and record change must share one direct cause.", "causation_mismatch");
  }

  if (
    input.recordChange.tenantId !== undefined &&
    input.outboxEntry.tenantId !== undefined &&
    input.recordChange.tenantId !== input.outboxEntry.tenantId
  ) {
    return invalidMutation("The outbox entry and record change must not cross tenant scope.", "tenant_mismatch");
  }

  if (
    input.recordChange.correlationId !== undefined &&
    input.outboxEntry.correlationId !== undefined &&
    input.recordChange.correlationId !== input.outboxEntry.correlationId
  ) {
    return invalidMutation("The outbox entry and record change must not conflict on correlation.", "correlation_mismatch");
  }

  return ok({
    recordChange: copyRecordChange(input.recordChange),
    outboxEntry: copyOutboxEntry(input.outboxEntry),
  });
}

function copyRecordChange(change: RecordChange): RecordChange {
  return {
    ...change,
    record: { ...change.record },
    ...(change.actor === undefined ? {} : { actor: { ...change.actor } }),
    ...(change.changedFields === undefined ? {} : { changedFields: [...change.changedFields] }),
  };
}

function copyOutboxEntry(entry: OutboxEntry): OutboxEntry {
  return {
    ...entry,
    subject: { ...entry.subject },
  };
}

function invalidMutation(
  defaultMessage: string,
  reason: string,
): Result<never, PlatformPersistenceError> {
  return err(
    platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
      defaultMessage,
      messageKey: "platform.persistence.transaction.mutation.invalid",
      params: { reason },
    }),
  );
}
