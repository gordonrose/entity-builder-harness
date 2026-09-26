import { deepEqual, equal, match } from "node:assert/strict";
import type { QueryResult, QueryResultRow } from "pg";
import {
  causationId,
  isoDateTimeFromDate,
  ok,
} from "@kanbien/core/shared";
import {
  outboxDeliveryPolicy,
  outboxEntry,
  outboxEntryId,
  outboxMessageType,
  recordChange,
  recordChangeId,
  recordId,
  recordKind,
  recordReference,
  recordRevision,
} from "@kanbien/core/persistence";
import {
  platformPersistenceLeaseOwner,
} from "@kanbien/platform-persistence";
import {
  createPostgreSqlMigrationRunner,
  createPostgreSqlPlatformPersistenceAtomicWriter,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceConfiguration,
  recordPostgreSqlPersistenceTelemetry,
  stagePostgreSqlTransactionStatement,
  withPostgreSqlTransaction,
  type PostgreSqlConnectionPool,
  type PostgreSqlStatement,
  type PostgreSqlTransactionalClient,
} from "../src/index";
import {
  postgreSqlPersistenceOperationError,
  postgreSqlPersistenceProviderFailureClass,
} from "../src/errors";
import {
  outboxInsertStatement,
  relation,
} from "../src/records";

async function main(): Promise<void> {
  const configuration = accepted(postgreSqlPersistenceConfiguration({
    host: "postgres.internal.example",
    port: 5432,
    database: "platform_smoke",
    schema: "platform_smoke",
    runtimeCredentialSecretReference: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:platform-smoke-runtime",
    maximumPoolSize: 4,
    connectionTimeoutMs: 1_000,
    idleTimeoutMs: 10_000,
    statementTimeoutMs: 5_000,
    tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
  }));
  const rejectedSecret = "this-must-not-appear-in-an-error";
  const invalid = postgreSqlPersistenceConfiguration({
    ...configuration,
    runtimeCredentialSecretReference: rejectedSecret,
  });
  equal(invalid.ok, false);
  if (!invalid.ok) equal(JSON.stringify(invalid.error).includes(rejectedSecret), false);

  equal(postgreSqlPersistenceProviderFailureClass({ code: "23505" }), "conflict");
  equal(postgreSqlPersistenceProviderFailureClass({ code: "ECONNREFUSED" }), "transport");
  deepEqual(
    postgreSqlPersistenceOperationError("claim_outbox", { code: "57014" }).params,
    { operation: "claim_outbox", provider_failure_class: "timeout" },
  );

  const at = (seconds: number) => isoDateTimeFromDate(new Date(Date.parse("2026-09-26T12:00:00.000Z") + (seconds * 1_000)));
  const subject = recordReference({
    kind: accepted(recordKind("platform-smoke.work-item")),
    id: accepted(recordId("work-value-$1")),
  });
  const entry = outboxEntry({
    id: outboxEntryId("outbox-1"),
    subject,
    messageType: accepted(outboxMessageType("platform-smoke.work.accepted")),
    deliveryPolicy: accepted(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
    createdAt: at(0),
    causationId: causationId("request-1"),
  });
  const change = accepted(recordChange({
    id: recordChangeId("change-1"),
    record: subject,
    revision: accepted(recordRevision(1)),
    action: "created",
    occurredAt: at(0),
    causationId: causationId("request-1"),
  }));
  const insert = outboxInsertStatement(configuration.schema, entry);
  match(insert.text, /VALUES \(\$1, \$2/);
  equal(insert.text.includes(String(subject.id)), false);
  equal(insert.values?.includes(String(subject.id)), true);
  let unsafeRelationRejected = false;
  try {
    relation("platform_smoke; DROP TABLE anything", "platform_outbox");
  } catch {
    unsafeRelationRejected = true;
  }
  equal(unsafeRelationRejected, true);

  const rollbackQueries: PostgreSqlStatement[] = [];
  const rollbackPool = recordingPool(rollbackQueries);
  const rolledBack = await withPostgreSqlTransaction({ pool: rollbackPool }, async () => ({ ok: false as const, error: "not-committed" }));
  equal(rolledBack.ok, false);
  deepEqual(rollbackQueries.map((query) => query.text), ["BEGIN", "ROLLBACK"]);

  const commitQueries: PostgreSqlStatement[] = [];
  const committed = await withPostgreSqlTransaction({ pool: recordingPool(commitQueries) }, async () => ok("committed"));
  equal(committed.ok, true);
  deepEqual(commitQueries.map((query) => query.text), ["BEGIN", "COMMIT"]);

  const observations: unknown[] = [];
  recordPostgreSqlPersistenceTelemetry((observation) => observations.push(observation), {
    operation: "write_atomic",
    outcome: "failed",
    durationMs: 14,
    poolInUse: 2,
    error: Object.assign(new Error("database password is not telemetry"), { code: "ECONNREFUSED" }),
  });
  deepEqual(observations, [{
    operation: "write_atomic",
    outcome: "failed",
    durationBucket: "under-100ms",
    errorClass: "transport",
    poolInUseBucket: "two-to-four",
  }]);
  equal(JSON.stringify(observations).includes("password"), false);

  const atomicQueries: PostgreSqlStatement[] = [];
  const atomic = createPostgreSqlPlatformPersistenceAtomicWriter(configuration.schema, { pool: recordingPool(atomicQueries) });
  const atomicResult = await atomic.run(async (scope) => {
    const participant = stagePostgreSqlTransactionStatement(scope.transaction, {
      text: "INSERT INTO \"platform_smoke\".\"synthetic_work_item\" (id) VALUES ($1)",
      values: ["opaque-work-1"],
    });
    if (!participant.ok) return participant;
    const staged = await scope.stage({ recordChange: change, outboxEntry: entry });
    if (!staged.ok) return staged;
    return ok("committed");
  });
  equal(atomicResult.ok, true);
  equal(atomicQueries.length, 5);
  equal(atomicQueries[0]?.text, "BEGIN");
  equal(atomicQueries[1]?.text, "INSERT INTO \"platform_smoke\".\"synthetic_work_item\" (id) VALUES ($1)");
  equal(atomicQueries[2]?.text.startsWith("INSERT INTO \"platform_smoke\".\"platform_record_change\""), true);
  equal(atomicQueries[3]?.text.startsWith("INSERT INTO \"platform_smoke\".\"platform_outbox\""), true);
  equal(atomicQueries[4]?.text, "COMMIT");

  const missingParticipantQueries: PostgreSqlStatement[] = [];
  const missingParticipant = await createPostgreSqlPlatformPersistenceAtomicWriter(configuration.schema, { pool: recordingPool(missingParticipantQueries) }).run(async (scope) => {
    const staged = await scope.stage({ recordChange: change, outboxEntry: entry });
    if (!staged.ok) return staged;
    return ok("not-committed");
  });
  equal(missingParticipant.ok, false);
  deepEqual(missingParticipantQueries.map((query) => query.text), ["BEGIN", "ROLLBACK"]);

  const migrationStatements: PostgreSqlStatement[] = [{ text: "CREATE TABLE \"platform_smoke\".\"synthetic_table\" (id text PRIMARY KEY)" }];
  const migration = { id: "v0001_synthetic_table", checksum: postgreSqlMigrationChecksum(migrationStatements), statements: migrationStatements };
  const migrationQueries: PostgreSqlStatement[] = [];
  const migrationRunner = createPostgreSqlMigrationRunner(configuration, { pool: recordingPool(migrationQueries) }, "adapter-v1");
  const migrationResult = await migrationRunner.apply({ schema: configuration.schema, migrations: [migration] });
  equal(migrationResult.ok, true);
  equal(migrationQueries.some((query) => query.text.includes("tool_version")), true);
  const checksumMismatchQueries: PostgreSqlStatement[] = [];
  const checksumMismatch = await createPostgreSqlMigrationRunner(
    configuration,
    { pool: checksumMismatchPool(checksumMismatchQueries) },
    "adapter-v1",
  ).apply({ schema: configuration.schema, migrations: [migration] });
  equal(checksumMismatch.ok, false);
  if (!checksumMismatch.ok) equal(checksumMismatch.error.code, "PLATFORM_PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH");
  equal(checksumMismatchQueries.at(-1)?.text, "ROLLBACK");
  const invalidChecksum = await migrationRunner.apply({
    schema: configuration.schema,
    migrations: [{ ...migration, checksum: "not-a-checksum" }],
  });
  equal(invalidChecksum.ok, false);
  const outOfOrderMigration = {
    id: "v0002_synthetic_table_second",
    checksum: postgreSqlMigrationChecksum([{ text: "CREATE TABLE \"platform_smoke\".\"synthetic_table_second\" (id text PRIMARY KEY)" }]),
    statements: [{ text: "CREATE TABLE \"platform_smoke\".\"synthetic_table_second\" (id text PRIMARY KEY)" }],
  };
  const outOfOrder = await migrationRunner.apply({
    schema: configuration.schema,
    migrations: [outOfOrderMigration, migration],
  });
  equal(outOfOrder.ok, false);

  equal(accepted(platformPersistenceLeaseOwner("worker-a")), "worker-a");
  console.log("PostgreSQL persistence adapter runtime test passed.");
}

function recordingPool(queries: PostgreSqlStatement[]): PostgreSqlConnectionPool {
  const client: PostgreSqlTransactionalClient = {
    query: async <TRow extends QueryResultRow>(statement: PostgreSqlStatement) => {
      queries.push(copyStatement(statement));
      return queryResult<TRow>();
    },
    release: () => undefined,
  };
  return {
    query: async <TRow extends QueryResultRow>(statement: PostgreSqlStatement) => {
      queries.push(copyStatement(statement));
      return queryResult<TRow>();
    },
    connect: async () => client,
    end: async () => undefined,
  };
}

function checksumMismatchPool(queries: PostgreSqlStatement[]): PostgreSqlConnectionPool {
  const query = async <TRow extends QueryResultRow>(statement: PostgreSqlStatement): Promise<QueryResult<TRow>> => {
    queries.push(copyStatement(statement));
    if (statement.text.startsWith("SELECT checksum")) {
      return { rows: [{ checksum: "0".repeat(64) }] } as unknown as QueryResult<TRow>;
    }
    return queryResult<TRow>();
  };
  const client: PostgreSqlTransactionalClient = { query, release: () => undefined };
  return { query, connect: async () => client, end: async () => undefined };
}

function queryResult<TRow extends QueryResultRow>(): QueryResult<TRow> {
  return { rows: [] } as unknown as QueryResult<TRow>;
}

function copyStatement(statement: PostgreSqlStatement): PostgreSqlStatement {
  return {
    text: statement.text,
    ...(statement.values === undefined ? {} : { values: [...statement.values] }),
  };
}

function accepted<TValue>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false }): TValue {
  if (!result.ok) throw new Error("Expected a valid test fixture.");
  return result.value;
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
