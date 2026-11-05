import type { Transaction } from "@kanbien/core/persistence";
import { err, ok, type Result } from "@kanbien/core/shared";
import {
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
import type { PostgreSqlConnectionPool, PostgreSqlStatement, PostgreSqlTransactionalClient } from "./connection";
import { postgreSqlPersistenceOperationError } from "./errors";
import { outboxInsertStatement, recordChangeInsertStatement } from "./records";
import { recordPostgreSqlPersistenceTelemetry, type PostgreSqlPersistenceTelemetrySink } from "./telemetry";
import { localRejection, observeBoundary } from "./observations";

export interface PostgreSqlTransactionOptions extends PlatformPersistenceDiagnosticOptions {
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
  readonly diagnostics: PlatformPersistenceDiagnosticOptions;
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
      return withPostgreSqlTransaction(options, async (client) => writePlatformFacts(client, schema, [validated.value], options));
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
    ) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>, invocationDiagnostics?: PlatformPersistenceDiagnosticOptions) => {
      const diagnostics = resolvePlatformPersistenceDiagnosticOptions(options, invocationDiagnostics);
      const buffer: PostgreSqlAtomicTransactionBuffer = {
        diagnostics,
        participantStatements: [],
        mutations: [],
        open: true,
      };
      const transaction: Transaction = {
        afterCommit: () => {
          const cause = new TypeError("PostgreSQL atomic persistence transactions do not permit callbacks; use the durable outbox for later work.");
          Object.assign(cause, localRejection(diagnostics, { operation: "write_atomic", field: "after-commit", condition: "unsupported", phase: "transaction-body", effect: "local-state-unchanged" }));
          throw cause;
        },
      };
      atomicTransactionBuffers.set(transaction, buffer);
      const scope: PlatformPersistenceTransactionScope = {
        transaction,
        stage: async (mutation) => {
          if (!buffer.open) return invalidAtomicTransaction("closed_scope", diagnostics, "transaction", "closed");
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
            return err(postgreSqlPersistenceOperationError("write_atomic", cause, diagnostics));
          } finally {
            buffer.open = false;
          }
          if (!operationResult.ok) return operationResult;
          if (buffer.participantStatements.length === 0) return invalidAtomicTransaction("missing_participant_statement", diagnostics, "participant", "missing");
          if (buffer.mutations.length === 0) return invalidAtomicTransaction("missing_platform_mutation", diagnostics, "mutation", "missing");
          try {
            for (const statement of buffer.participantStatements) await client.query(statement);
            const facts = await writePlatformFacts(client, schema, buffer.mutations, diagnostics);
            if (!facts.ok) return facts;
            return operationResult;
          } catch (cause) {
            return err(postgreSqlPersistenceOperationError("write_atomic", cause, diagnostics));
          }
        }, diagnostics);
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
  if (buffer === undefined || !buffer.open) return invalidAtomicTransaction("unsupported_transaction", buffer?.diagnostics, "transaction", buffer === undefined ? "unsupported" : "closed", "statement-selection");
  const rejected = rejectedDmlStatement(statement);
  if (rejected !== undefined) return invalidAtomicTransaction("invalid_participant_statement", buffer.diagnostics, "statement", rejected, "statement-selection");
  buffer.participantStatements.push({
    text: statement.text,
    ...(statement.values === undefined ? {} : { values: [...statement.values] }),
  });
  return ok(undefined);
}

export async function withPostgreSqlTransaction<TValue, TFailure>(
  options: PostgreSqlTransactionOptions,
  operation: (client: PostgreSqlTransactionalClient) => Promise<Result<TValue, TFailure>> | Result<TValue, TFailure>,
  diagnostics: PlatformPersistenceDiagnosticOptions = options,
): Promise<Result<TValue, TFailure | PlatformPersistenceError>> {
  const startedAt = performance.now();
  let client: PostgreSqlTransactionalClient | undefined;
  let began = false;
  let boundary: "acquire" | "begin" | "body" | "commit" | "rollback" = "acquire";
  let effect: "not-started" | "transaction-open" | "commit-completed" | "rollback-completed" | "unknown" = "not-started";
  try {
    client = await options.pool.connect();
    boundary = "begin";
    await client.query({ text: "BEGIN" });
    began = true;
    effect = "transaction-open";
    boundary = "body";
    const result = await operation(client);
    if (!result.ok) {
      observeBoundary(diagnostics, { operation: "transaction", phase: "returned-result", boundary: "body", condition: "returned-failure", effect: "unknown" }, failureData(result));
      boundary = "rollback";
      await client.query({ text: "ROLLBACK" });
      effect = "rollback-completed";
      recordPostgreSqlPersistenceTelemetry(options.telemetry, {
        operation: "transaction",
        outcome: "rolled_back",
        durationMs: performance.now() - startedAt,
      }, diagnostics);
      return result;
    }
    boundary = "commit";
    effect = "unknown";
    await client.query({ text: "COMMIT" });
    effect = "commit-completed";
    recordPostgreSqlPersistenceTelemetry(options.telemetry, {
      operation: "transaction",
      outcome: "succeeded",
      durationMs: performance.now() - startedAt,
    }, diagnostics);
    return result;
  } catch (cause) {
    observeBoundary(diagnostics, { operation: "transaction", phase: "invocation", boundary, condition: "rejected", effect: boundary === "acquire" ? "not-started" : "unknown" }, cause);
    effect = boundary === "acquire" ? "not-started" : "unknown";
    if (began && client !== undefined) {
      try {
        await client.query({ text: "ROLLBACK" });
        effect = "rollback-completed";
      } catch (rollbackCause) {
        observeBoundary(diagnostics, { operation: "transaction", phase: "invocation", boundary: "recovery-rollback", condition: "rejected", effect: "unknown" }, rollbackCause);
      }
    }
    recordPostgreSqlPersistenceTelemetry(options.telemetry, {
      operation: "transaction",
      outcome: "failed",
      durationMs: performance.now() - startedAt,
      error: cause,
    }, diagnostics);
    return {
      ok: false,
      error: postgreSqlPersistenceOperationError("transaction", cause, diagnostics, undefined, "native-only"),
    };
  } finally {
    try { client?.release(); }
    catch (cause) { observeBoundary(diagnostics, { operation: "transaction", phase: "invocation", boundary: "release", condition: "threw", effect }, cause); throw cause; }
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
  diagnostics?: PlatformPersistenceDiagnosticOptions,
): Promise<Result<void, PlatformPersistenceError>> {
  try {
    for (const mutation of mutations) {
      await client.query(recordChangeInsertStatement(schema, mutation.recordChange));
      await client.query(outboxInsertStatement(schema, mutation.outboxEntry));
    }
    return ok(undefined);
  } catch (cause) {
    return err(postgreSqlPersistenceOperationError("write_facts", cause, diagnostics));
  }
}

function invalidAtomicTransaction(reason: string, diagnostics?: PlatformPersistenceDiagnosticOptions,
  field: PersistenceLocalRejectionDetail["field"] = "transaction", condition: PersistenceLocalRejectionDetail["condition"] = "unsupported",
  phase: PersistenceLocalRejectionDetail["phase"] = "transaction-body"): Result<never, PlatformPersistenceError> {
  return err(platformPersistenceError({
    code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
    defaultMessage: "The PostgreSQL atomic persistence transaction is incomplete or invalid.",
    messageKey: "platform.persistence.transaction.atomic.invalid",
    params: { reason },
    ...localRejection(diagnostics, { operation: "write_atomic", field, condition, phase, effect: "local-state-unchanged" }),
  }));
}

function rejectedDmlStatement(statement: PostgreSqlStatement): PersistenceLocalRejectionDetail["condition"] | undefined {
  const text = statement.text.trim();
  if (text.length === 0) return "empty";
  if (text.length > 10_000) return "too-long";
  if (text.includes(";")) return "semicolon";
  if (text.includes("\u0000")) return "nul";
  if (!/^(?:INSERT|UPDATE|DELETE)\s/i.test(text)) return "unsupported-verb";
  return undefined;
}

function failureData(result: unknown): unknown {
  try { const error = Object.getOwnPropertyDescriptor(result, "error"); return error && "value" in error ? error.value : undefined; }
  catch { return undefined; }
}
