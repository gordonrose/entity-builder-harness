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
  resolvePlatformPersistenceDiagnosticOptions,
  type PlatformPersistenceAtomicWriter,
  type PlatformPersistenceError,
  type PlatformPersistenceMutation,
  type PlatformPersistenceTransactionScope,
  type PlatformPersistenceDiagnosticOptions,
  type PersistenceLocalRejectionDetail,
} from "@kanbien/platform-persistence";
import type { DynamoDbPersistenceCommandClient } from "./client";
import type { DynamoDbPersistenceConfiguration } from "./configuration/index";
import { outboxRecordToItem, recordChangeToItem } from "./records";
import { dynamoDbObservation, type DynamoDbObservation } from "./observations";

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

export interface DynamoDbPlatformPersistenceFactWriterOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

/**
 * A provider-specific writer that fulfils Platform's atomic-writer port.
 * Target composition supplies product-state writes using the deliberately
 * adapter-local `stageDynamoDbTransactionWrite` seam.
 */
export interface DynamoDbPlatformPersistenceAtomicWriter extends PlatformPersistenceAtomicWriter {}

export interface DynamoDbPlatformPersistenceAtomicWriterOptions extends PlatformPersistenceDiagnosticOptions {
  readonly configuration: DynamoDbPersistenceConfiguration;
  readonly client: DynamoDbPersistenceCommandClient;
}

interface DynamoDbAtomicTransactionBuffer {
  readonly observation: DynamoDbObservation;
  readonly participantWrites: TransactWriteItem[];
  readonly mutations: PlatformPersistenceMutation[];
  open: boolean;
}

export function createDynamoDbPlatformPersistenceFactWriter(
  options: DynamoDbPlatformPersistenceFactWriterOptions,
): DynamoDbPlatformPersistenceFactWriter {
  return {
    write: async (mutation) => {
      const observed = dynamoDbObservation(options, "write_facts");
      try {
        await observed.send(options, () => dynamoDbPlatformPersistenceFactTransaction(options.configuration, mutation));
        return ok(undefined);
      } catch {
        return err(observed.error("write_facts"));
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
      invocationDiagnostics?: PlatformPersistenceDiagnosticOptions,
    ): Promise<Result<TValue, TFailure | PlatformPersistenceError>> {
      const diagnostics = resolvePlatformPersistenceDiagnosticOptions(options, invocationDiagnostics);
      const observed = dynamoDbObservation(diagnostics, "write_atomic");
      const buffer: DynamoDbAtomicTransactionBuffer = {
        observation: observed,
        participantWrites: [],
        mutations: [],
        open: true,
      };
      const transaction: Transaction = {
        afterCommit: () => {
          throw Object.assign(new TypeError("DynamoDB atomic persistence transactions do not permit callbacks; use the durable outbox for later work."), observed.reject("after-commit", "unsupported", "transaction-body", "local-state-unchanged"));
        },
      };
      atomicTransactionBuffers.set(transaction, buffer);
      const scope: PlatformPersistenceTransactionScope = {
        transaction,
        stage: async (mutation) => {
          if (!buffer.open) return invalidAtomicTransaction("closed_scope", observed, "transaction", "closed");
          const validated = platformPersistenceMutation(mutation);
          if (!validated.ok) {
            const source = Object.getOwnPropertyDescriptor(validated, "error");
            observed.source(source !== undefined && "value" in source ? source.value : undefined);
            return validated;
          }
          if (buffer.participantWrites.length + ((buffer.mutations.length + 1) * 2) > maximumDynamoDbTransactionWrites) {
            return invalidAtomicTransaction("write_limit", observed, "mutation", "too-large");
          }
          buffer.mutations.push(validated.value);
          return ok(validated.value);
        },
      };

      let operationResult: Result<TValue, TFailure>;
      try {
        operationResult = await operation(scope);
      } catch (cause) {
        observed.observe("callback", cause);
        buffer.open = false;
        atomicTransactionBuffers.delete(transaction);
        return err(observed.error("write_atomic"));
      }
      buffer.open = false;

      if (!operationResult.ok) {
        let cause: unknown;
        try { const field = Object.getOwnPropertyDescriptor(operationResult, "error"); cause = field && "value" in field ? field.value : undefined; } catch { /* Optional source is unavailable. */ }
        observed.observe("callback", cause);
        atomicTransactionBuffers.delete(transaction);
        return operationResult;
      }
      if (buffer.participantWrites.length === 0) {
        atomicTransactionBuffers.delete(transaction);
        return invalidAtomicTransaction("missing_participant_write", observed, "participant", "missing");
      }
      if (buffer.mutations.length === 0) {
        atomicTransactionBuffers.delete(transaction);
        return invalidAtomicTransaction("missing_platform_mutation", observed, "mutation", "missing");
      }

      try {
        await observed.send(options, () => dynamoDbPlatformPersistenceAtomicTransaction(options.configuration, {
          participantWrites: buffer.participantWrites,
          mutations: buffer.mutations,
        }));
        return operationResult;
      } catch {
        return err(observed.error("write_atomic"));
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
  if (buffer === undefined || !buffer.open) return invalidAtomicTransaction("unsupported_transaction", buffer?.observation, "transaction", buffer === undefined ? "unsupported" : "closed", "statement-selection");
  let count: number;
  try { count = dynamoDbTransactionWriteCount(write); }
  catch (cause) { buffer.observation.observe("encoding", cause); throw cause; }
  if (count !== 1) return invalidAtomicTransaction("invalid_participant_write", buffer.observation, "participant", count === 0 ? "absent" : typeof count === "number" && count > 1 ? "too-large" : "predicate-rejected", "statement-selection");
  if (buffer.participantWrites.length + 1 + (buffer.mutations.length * 2) > maximumDynamoDbTransactionWrites) {
    return invalidAtomicTransaction("write_limit", buffer.observation, "participant", "too-large", "statement-selection");
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
  observation = dynamoDbObservation(undefined, "write_atomic"),
  field: PersistenceLocalRejectionDetail["field"] = "transaction",
  condition: PersistenceLocalRejectionDetail["condition"] = "unsupported",
  phase: PersistenceLocalRejectionDetail["phase"] = "transaction-body",
): Result<never, PlatformPersistenceError> {
  return err(platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
    defaultMessage: "The atomic persistence transaction is incomplete or invalid.",
    messageKey: "platform.persistence.transaction.atomic.invalid",
    params: { reason },
    ...observation.reject(field, condition, phase, "local-state-unchanged"),
  }));
}

function dynamoDbTransactionWriteCount(write: TransactWriteItem): number {
  return [write.Put, write.Update, write.Delete, write.ConditionCheck]
    .filter((operation) => operation !== undefined)
    .length;
}
