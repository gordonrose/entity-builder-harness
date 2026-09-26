import type { Transaction } from "@kanbien/core/persistence";
import { err, ok, type Result } from "@kanbien/core/shared";
import {
  platformPersistenceError,
  platformPersistenceMutation,
  type PlatformPersistenceAtomicWriter,
  type PlatformPersistenceError,
  type PlatformPersistenceMutation,
  type PlatformPersistenceTransactionScope,
} from "@kanbien/platform-persistence";
import type { PostgreSqlConnectionPool, PostgreSqlStatement, PostgreSqlTransactionalClient } from "./connection";
import { postgreSqlPersistenceOperationError } from "./errors";
import { outboxInsertStatement, recordChangeInsertStatement } from "./records";
import { recordPostgreSqlPersistenceTelemetry, type PostgreSqlPersistenceTelemetrySink } from "./telemetry";

export interface PostgreSqlTransactionOptions {
  readonly pool: PostgreSqlConnectionPool;
  readonly telemetry?: PostgreSqlPersistenceTelemetrySink;
}

/**
 * The fact writer protects only the two platform-owned facts. Product state
 * belongs to an application repository and joins the stricter atomic writer.
 */
export interface PostgreSqlPlatformPersistenceFactWriter {
  write(mutation: PlatformPersistenceMutation): Promise<Result<void, PlatformPersistenceError>>;
}

export interface PostgreSqlPlatformPersistenceAtomicWriter extends PlatformPersistenceAtomicWriter {}

interface PostgreSqlAtomicTransactionBuffer {
  readonly participantStatements: PostgreSqlStatement[];
  readonly mutations: PlatformPersistenceMutation[];
  open: boolean;
}

const atomicTransactionBuffers = new WeakMap<Transaction, PostgreSqlAtomicTransactionBuffer>();

export function createPostgreSqlPlatformPersistenceFactWriter(
  schema: string,
  options: PostgreSqlTransactionOptions,
): PostgreSqlPlatformPersistenceFactWriter {
  return {
    write: async (mutation) => {
      const validated = platformPersistenceMutation(mutation);
      if (!validated.ok) return validated;
      return withPostgreSqlTransaction(options, async (client) => writePlatformFacts(client, schema, [validated.value]));
    },
  };
}

/**
 * Provides one provider-local transaction scope. Product composition can add
 * reviewed DML statements, then stages the provider-neutral lineage/outbox
 * mutation through the generic Platform scope before the adapter commits all
 * participants together.
 */
export function createPostgreSqlPlatformPersistenceAtomicWriter(
  schema: string,
  options: PostgreSqlTransactionOptions,
): PostgreSqlPlatformPersistenceAtomicWriter {
  return {
    run: async <TValue, TFailure>(operation: (
      scope: PlatformPersistenceTransactionScope,
    ) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>) => {
      const buffer: PostgreSqlAtomicTransactionBuffer = {
        participantStatements: [],
        mutations: [],
        open: true,
      };
      const transaction: Transaction = {
        afterCommit: () => {
          throw new TypeError("PostgreSQL atomic persistence transactions do not permit callbacks; use the durable outbox for later work.");
        },
      };
      atomicTransactionBuffers.set(transaction, buffer);
      const scope: PlatformPersistenceTransactionScope = {
        transaction,
        stage: async (mutation) => {
          if (!buffer.open) return invalidAtomicTransaction("closed_scope");
          const validated = platformPersistenceMutation(mutation);
          if (!validated.ok) return validated;
          buffer.mutations.push(validated.value);
          return ok(validated.value);
        },
      };

      try {
        return await withPostgreSqlTransaction<TValue, TFailure | PlatformPersistenceError>(options, async (client) => {
          let operationResult: Result<TValue, TFailure>;
          try {
            operationResult = await operation(scope);
          } catch (cause) {
            return err(postgreSqlPersistenceOperationError("write_atomic", cause));
          } finally {
            buffer.open = false;
          }
          if (!operationResult.ok) return operationResult;
          if (buffer.participantStatements.length === 0) return invalidAtomicTransaction("missing_participant_statement");
          if (buffer.mutations.length === 0) return invalidAtomicTransaction("missing_platform_mutation");
          try {
            for (const statement of buffer.participantStatements) await client.query(statement);
            const facts = await writePlatformFacts(client, schema, buffer.mutations);
            if (!facts.ok) return facts;
            return operationResult;
          } catch (cause) {
            return err(postgreSqlPersistenceOperationError("write_atomic", cause));
          }
        });
      } finally {
        buffer.open = false;
        atomicTransactionBuffers.delete(transaction);
      }
    },
  };
}

/**
 * This is intentionally adapter-local. It accepts only one reviewed DML
 * statement with bind values; it cannot stage DDL, transaction control, or
 * multiple statements supplied by a request.
 */
export function stagePostgreSqlTransactionStatement(
  transaction: Transaction,
  statement: PostgreSqlStatement,
): Result<void, PlatformPersistenceError> {
  const buffer = atomicTransactionBuffers.get(transaction);
  if (buffer === undefined || !buffer.open) return invalidAtomicTransaction("unsupported_transaction");
  if (!isReviewedDmlStatement(statement)) return invalidAtomicTransaction("invalid_participant_statement");
  buffer.participantStatements.push({
    text: statement.text,
    ...(statement.values === undefined ? {} : { values: [...statement.values] }),
  });
  return ok(undefined);
}

export async function withPostgreSqlTransaction<TValue, TFailure>(
  options: PostgreSqlTransactionOptions,
  operation: (client: PostgreSqlTransactionalClient) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>,
): Promise<Result<TValue, TFailure | PlatformPersistenceError>> {
  const startedAt = performance.now();
  let client: PostgreSqlTransactionalClient | undefined;
  let began = false;
  try {
    client = await options.pool.connect();
    await client.query({ text: "BEGIN" });
    began = true;
    const result = await operation(client);
    if (!result.ok) {
      await client.query({ text: "ROLLBACK" });
      recordPostgreSqlPersistenceTelemetry(options.telemetry, {
        operation: "transaction",
        outcome: "rolled_back",
        durationMs: performance.now() - startedAt,
      });
      return result;
    }
    await client.query({ text: "COMMIT" });
    recordPostgreSqlPersistenceTelemetry(options.telemetry, {
      operation: "transaction",
      outcome: "succeeded",
      durationMs: performance.now() - startedAt,
    });
    return result;
  } catch (cause) {
    if (began && client !== undefined) {
      try {
        await client.query({ text: "ROLLBACK" });
      } catch {
        // The original failure remains the safe result; rollback failure is telemetry-only.
      }
    }
    recordPostgreSqlPersistenceTelemetry(options.telemetry, {
      operation: "transaction",
      outcome: "failed",
      durationMs: performance.now() - startedAt,
      error: cause,
    });
    return {
      ok: false,
      error: postgreSqlPersistenceOperationError("transaction", cause),
    };
  } finally {
    client?.release();
  }
}

export function postgreSqlTransactionFailure(
  defaultMessage: string,
): Result<never, PlatformPersistenceError> {
  return {
    ok: false,
    error: platformPersistenceError({
      code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
      defaultMessage,
      messageKey: "platform.persistence.transaction.postgresql.invalid",
    }),
  };
}

async function writePlatformFacts(
  client: PostgreSqlTransactionalClient,
  schema: string,
  mutations: readonly PlatformPersistenceMutation[],
): Promise<Result<void, PlatformPersistenceError>> {
  try {
    for (const mutation of mutations) {
      await client.query(recordChangeInsertStatement(schema, mutation.recordChange));
      await client.query(outboxInsertStatement(schema, mutation.outboxEntry));
    }
    return ok(undefined);
  } catch (cause) {
    return err(postgreSqlPersistenceOperationError("write_facts", cause));
  }
}

function invalidAtomicTransaction(reason: string): Result<never, PlatformPersistenceError> {
  return err(platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
    defaultMessage: "The PostgreSQL atomic persistence transaction is incomplete or invalid.",
    messageKey: "platform.persistence.transaction.atomic.invalid",
    params: { reason },
  }));
}

function isReviewedDmlStatement(statement: PostgreSqlStatement): boolean {
  const text = statement.text.trim();
  return text.length > 0
    && text.length <= 10_000
    && !text.includes(";")
    && !text.includes("\u0000")
    && /^(?:INSERT|UPDATE|DELETE)\s/i.test(text);
}
