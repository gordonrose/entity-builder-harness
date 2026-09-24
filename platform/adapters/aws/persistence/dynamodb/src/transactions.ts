import {
  TransactWriteItemsCommand,
  type TransactWriteItem,
} from "@aws-sdk/client-dynamodb";
import type { Transaction } from "@kanbien/core/persistence";
import { err, ok, type Result } from "@kanbien/core/shared";
import {
  platformOutboxRecord,
  platformPersistenceError,
  platformPersistenceMutation,
  type PlatformPersistenceAtomicWriter,
  type PlatformPersistenceError,
  type PlatformPersistenceMutation,
  type PlatformPersistenceTransactionScope,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration";
import { dynamoDbPersistenceOperationError } from "./errors";
import { outboxRecordToItem, recordChangeToItem } from "./records";

const maximumDynamoDbTransactionWrites = 100;
const atomicTransactionBuffers = new WeakMap<Transaction, DynamoDbAtomicTransactionBuffer>();

/**
 * Atomically persists the two platform-owned immutable facts in a mutation.
 * It intentionally is not a general entity repository: a real product state
 * write must participate through the atomic-writer seam below.
 */
export interface DynamoDbPlatformPersistenceFactWriter {
  write(mutation: PlatformPersistenceMutation): Promise<Result<void, PlatformPersistenceError>>;
}

export interface DynamoDbPlatformPersistenceFactWriterOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

/**
 * A provider-specific writer that fulfils Platform's atomic-writer port.
 * Target composition supplies product-state writes using the deliberately
 * adapter-local `stageDynamoDbTransactionWrite` seam.
 */
export interface DynamoDbPlatformPersistenceAtomicWriter extends PlatformPersistenceAtomicWriter {}

export interface DynamoDbPlatformPersistenceAtomicWriterOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

interface DynamoDbAtomicTransactionBuffer {
  readonly participantWrites: TransactWriteItem[];
  readonly mutations: PlatformPersistenceMutation[];
  open: boolean;
}

export function createDynamoDbPlatformPersistenceFactWriter(
  options: DynamoDbPlatformPersistenceFactWriterOptions,
): DynamoDbPlatformPersistenceFactWriter {
  return {
    write: async (mutation) => {
      try {
        await options.client.send(dynamoDbPlatformPersistenceFactTransaction(options.configuration, mutation));
        return ok(undefined);
      } catch {
        return err(dynamoDbPersistenceOperationError("write_facts"));
      }
    },
  };
}

/**
 * Build a transaction scope which requires both a product-state participant
 * and at least one validated platform mutation before it sends anything.
 */
export function createDynamoDbPlatformPersistenceAtomicWriter(
  options: DynamoDbPlatformPersistenceAtomicWriterOptions,
): DynamoDbPlatformPersistenceAtomicWriter {
  return {
    async run<TValue, TFailure>(
      operation: (
        scope: PlatformPersistenceTransactionScope,
      ) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>,
    ): Promise<Result<TValue, TFailure | PlatformPersistenceError>> {
      const buffer: DynamoDbAtomicTransactionBuffer = {
        participantWrites: [],
        mutations: [],
        open: true,
      };
      const transaction: Transaction = {
        afterCommit: () => {
          throw new TypeError("DynamoDB atomic persistence transactions do not permit callbacks; use the durable outbox for later work.");
        },
      };
      atomicTransactionBuffers.set(transaction, buffer);
      const scope: PlatformPersistenceTransactionScope = {
        transaction,
        stage: async (mutation) => {
          if (!buffer.open) return invalidAtomicTransaction("closed_scope");
          const validated = platformPersistenceMutation(mutation);
          if (!validated.ok) return validated;
          if (buffer.participantWrites.length + ((buffer.mutations.length + 1) * 2) > maximumDynamoDbTransactionWrites) {
            return invalidAtomicTransaction("write_limit");
          }
          buffer.mutations.push(validated.value);
          return ok(validated.value);
        },
      };

      let operationResult: Result<TValue, TFailure>;
      try {
        operationResult = await operation(scope);
      } catch {
        buffer.open = false;
        atomicTransactionBuffers.delete(transaction);
        return err(dynamoDbPersistenceOperationError("write_atomic"));
      }
      buffer.open = false;

      if (!operationResult.ok) {
        atomicTransactionBuffers.delete(transaction);
        return operationResult;
      }
      if (buffer.participantWrites.length === 0) {
        atomicTransactionBuffers.delete(transaction);
        return invalidAtomicTransaction("missing_participant_write");
      }
      if (buffer.mutations.length === 0) {
        atomicTransactionBuffers.delete(transaction);
        return invalidAtomicTransaction("missing_platform_mutation");
      }

      try {
        await options.client.send(dynamoDbPlatformPersistenceAtomicTransaction(options.configuration, {
          participantWrites: buffer.participantWrites,
          mutations: buffer.mutations,
        }));
        return operationResult;
      } catch {
        return err(dynamoDbPersistenceOperationError("write_atomic"));
      } finally {
        atomicTransactionBuffers.delete(transaction);
      }
    },
  };
}

/**
 * Target-only composition uses this function to enlist one product write in
 * the exact transaction scope received by a transaction-aware repository.
 */
export function stageDynamoDbTransactionWrite(
  transaction: Transaction,
  write: TransactWriteItem,
): Result<void, PlatformPersistenceError> {
  const buffer = atomicTransactionBuffers.get(transaction);
  if (buffer === undefined || !buffer.open) return invalidAtomicTransaction("unsupported_transaction");
  if (!isOneDynamoDbTransactionWrite(write)) return invalidAtomicTransaction("invalid_participant_write");
  if (buffer.participantWrites.length + 1 + (buffer.mutations.length * 2) > maximumDynamoDbTransactionWrites) {
    return invalidAtomicTransaction("write_limit");
  }
  buffer.participantWrites.push(write);
  return ok(undefined);
}

export function dynamoDbPlatformPersistenceFactTransaction(
  configuration: DynamoDbPersistenceConfiguration,
  mutation: PlatformPersistenceMutation,
): TransactWriteItemsCommand {
  return dynamoDbPlatformPersistenceAtomicTransaction(configuration, {
    participantWrites: [],
    mutations: [mutation],
  });
}

export function dynamoDbPlatformPersistenceAtomicTransaction(
  configuration: DynamoDbPersistenceConfiguration,
  input: {
    readonly participantWrites: readonly TransactWriteItem[];
    readonly mutations: readonly PlatformPersistenceMutation[];
  },
): TransactWriteItemsCommand {
  return new TransactWriteItemsCommand({
    TransactItems: [
      ...input.participantWrites,
      ...input.mutations.flatMap((mutation) => [
        {
          Put: {
            TableName: configuration.tableName,
            Item: recordChangeToItem(mutation.recordChange),
            ConditionExpression: "attribute_not_exists(#pk)",
            ExpressionAttributeNames: { "#pk": "PK" },
          },
        },
        {
          Put: {
            TableName: configuration.tableName,
            Item: outboxRecordToItem(platformOutboxRecord({ entry: mutation.outboxEntry })),
            ConditionExpression: "attribute_not_exists(#pk)",
            ExpressionAttributeNames: { "#pk": "PK" },
          },
        },
      ]),
    ],
  });
}

function invalidAtomicTransaction(
  reason: string,
): Result<never, PlatformPersistenceError> {
  return err(platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
    defaultMessage: "The atomic persistence transaction is incomplete or invalid.",
    messageKey: "platform.persistence.transaction.atomic.invalid",
    params: { reason },
  }));
}

function isOneDynamoDbTransactionWrite(write: TransactWriteItem): boolean {
  return [write.Put, write.Update, write.Delete, write.ConditionCheck]
    .filter((operation) => operation !== undefined)
    .length === 1;
}
