import { deepEqual, equal, match, rejects, throws } from "node:assert/strict";
import { EventEmitter } from "node:events";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import * as coreConfig from "@kanbien/core/config";
import { createDiagnosticRecord, defineDiagnostic, type DiagnosticRecord } from "@kanbien/core/diagnostics";
import { platformSecurityDiagnosticCatalog } from "@kanbien/platform-security";
import { Pool, type QueryResult, type QueryResultRow } from "pg";
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
  platformPersistenceFence,
  type PlatformPersistenceTransactionScope,
  type PlatformPersistenceDiagnosticOptions,
} from "@kanbien/platform-persistence";
import {
  createPostgreSqlMigrationRunner,
  createPostgreSqlPlatformPersistenceAtomicWriter,
  createPostgreSqlPlatformOutboxStore,
  createPostgreSqlPlatformProcessingStore,
  createPostgreSqlPlatformRecordChangeStore,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceConfiguration,
  postgreSqlPersistenceRequirements,
  assemblePostgreSqlPersistenceConfiguration,
  postgreSqlPasswordCredentials,
  postgreSqlLoginNameRule,
  postgreSqlPersistenceConfigurationTextRules,
  rdsIamAuthenticationTextRules,
  postgreSqlPlatformPersistenceObserver,
  recordPostgreSqlPersistenceTelemetry,
  stagePostgreSqlTransactionStatement,
  withPostgreSqlTransaction,
  type PostgreSqlConnectionPool,
  type PostgreSqlStatement,
  type PostgreSqlTransactionalClient,
  type PostgreSqlPersistenceConfiguration,
  type PostgreSqlPersistenceTelemetry,
} from "../src/index";
import { nodePoolAdapter, nodeClientAdapter } from "../src/connection";
import * as groupedConfiguration from "../src/configuration/index";

equal(postgreSqlPersistenceConfiguration, groupedConfiguration.postgreSqlPersistenceConfiguration);
equal(postgreSqlPersistenceRequirements, groupedConfiguration.postgreSqlPersistenceRequirements);
equal(assemblePostgreSqlPersistenceConfiguration, groupedConfiguration.assemblePostgreSqlPersistenceConfiguration);
equal(postgreSqlLoginNameRule, groupedConfiguration.postgreSqlLoginNameRule);
equal(postgreSqlPersistenceConfigurationTextRules, groupedConfiguration.postgreSqlPersistenceConfigurationTextRules);
import { storedObservation } from "../src/observations";
import {
  postgreSqlPersistenceOperationError,
  postgreSqlPersistenceProviderFailureClass,
} from "../src/errors";
import {
  outboxInsertStatement,
  relation,
  outboxRecordFromRow,
  processingRecordFromRow,
  recordChangeFromRow,
  type PostgreSqlOutboxRow,
  type PostgreSqlProcessingRow,
  type PostgreSqlLineageRow,
} from "../src/records";

function destinationPortBinding(configuration: PostgreSqlPersistenceConfiguration): void {
  const filename = require.resolve("../src/configuration/domain/validation");
  const localRequire = createRequire(filename);
  const fixture = { exports: {} as { postgreSqlPersistenceConfiguration: typeof postgreSqlPersistenceConfiguration } };
  const narrowed = Object.freeze({ ...coreConfig.destinationPortConstraint, minimum: 2, maximum: 65_534 });
  // Execute only the trusted compiled consumer; the real Core contract stays frozen and unchanged.
  new Function("require", "module", "exports", readFileSync(filename, "utf8"))(
    (name: string) => name === "@kanbien/core/config" ? { ...coreConfig, destinationPortConstraint: narrowed } : localRequire(name),
    fixture, fixture.exports,
  );
  const check = fixture.exports.postgreSqlPersistenceConfiguration;
  for (const port of [2, 5432, 65_534]) equal(check({ ...configuration, port }).ok, true);
  for (const port of [1, 65_535]) {
    const rejected = check({ ...configuration, port });
    equal(rejected.ok, false, "copied port bounds must fail this shared-binding counterexample");
    if (!rejected.ok) equal(rejected.error.details.reasonCode, "out-of-range");
  }
  deepEqual(coreConfig.destinationPortConstraint, { kind: "integer", minimum: 1, maximum: 65_535 });
}

async function main(): Promise<void> {
  equal(rdsIamAuthenticationTextRules.username, postgreSqlLoginNameRule, "IAM and password credentials share the same login policy");
  for (const [username, expected] of [["_", true], ["_".repeat(63), true], ["_".repeat(64), false], ["user", true], ["User", false], ["bad-user", false], [" user", false]] as const) {
    equal(postgreSqlLoginNameRule.pattern.test(username), expected);
    equal(postgreSqlPasswordCredentials({ username, password: "synthetic" }).ok, expected);
    equal(rdsIamAuthenticationTextRules.username.pattern.test(username), expected);
  }
  equal(postgreSqlPersistenceConfigurationTextRules.database.pattern.test("_"), false, "database identifier policy must not widen");
  equal(postgreSqlPersistenceConfigurationTextRules.schema.pattern.test("_"), false, "schema identifier policy must not widen");
  for (const [field, values] of Object.entries({
    username: [[undefined, "missing"], [null, "wrong-type"], [42, "wrong-type"], [[], "wrong-type"], ["", "blank"], [" \t", "blank"], [" user", "surrounding-whitespace"], ["user\n", "surrounding-whitespace"], ["bad-user", "invalid-format"], ["_".repeat(64), "invalid-format"]],
    password: [[undefined, "missing"], [null, "wrong-type"], [42, "wrong-type"], [{}, "wrong-type"], ["", "empty"], ["synthetic-private\u0000password", "forbidden-character"]],
  })) for (const [value, reason] of values) {
    const result = postgreSqlPasswordCredentials({ username: "synthetic_user", password: "synthetic-private-password", [field]: value });
    deepEqual(result, { ok: false, error: { issues: [{ field, reason }] } });
    equal(JSON.stringify(result).includes("synthetic"), false);
  }
  deepEqual(postgreSqlPasswordCredentials({}), { ok: false, error: { issues: [{ field: "username", reason: "missing" }, { field: "password", reason: "missing" }] } });
  let credentialAccessorRead = false;
  const accessor = Object.defineProperty({ password: "synthetic" }, "username", { get() { credentialAccessorRead = true; throw new Error("synthetic-private"); } });
  deepEqual(postgreSqlPasswordCredentials(accessor), { ok: false, error: { issues: [{ field: "username", reason: "wrong-type" }] } });
  equal(credentialAccessorRead, false);
  for (const username of ["_", "_".repeat(63), "user"]) for (const password of [" ", "\t\n", " synthetic password ", "päss😀", "x".repeat(10000)]) {
    deepEqual(postgreSqlPasswordCredentials({ username, password, extra: "ignored" }), { ok: true, value: { username, password } }, "historically accepted values are unchanged");
  }
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
  deepEqual(postgreSqlPersistenceRequirements.map(item => item.setting), ["database.host", "database.port", "database.name", "database.schema", "authentication.reference"]);
  const logical = { "database.host": configuration.host, "database.port": configuration.port, "database.name": configuration.database,
    "database.schema": configuration.schema, "authentication.reference": configuration.runtimeCredentialSecretReference };
  const extraPolicy = { ...configuration, host: "synthetic-unchecked-canary" };
  deepEqual(assemblePostgreSqlPersistenceConfiguration(logical, extraPolicy), { ok: true, value: configuration },
    "only explicit policy fields may be used; unchecked extras must not override checked values");
  const omittedPort = { ...logical }; delete (omittedPort as Partial<typeof logical>)["database.port"];
  const omittedResult = assemblePostgreSqlPersistenceConfiguration(omittedPort, configuration);
  equal(omittedResult.ok, false);
  if (!omittedResult.ok) equal(omittedResult.error.details.reasonCode, "missing");
  const rejectedSecret = "this-must-not-appear-in-an-error";
  for (const port of [1, 5432, 65_535]) equal(postgreSqlPersistenceConfiguration({ ...configuration, port }).ok, true);
  for (const [value, reason] of [[undefined, "missing"], ["5432", "wrong-type"], [1.5, "invalid-integer"],
    [NaN, "invalid-integer"], [Infinity, "invalid-integer"], [-Infinity, "invalid-integer"],
    [0, "out-of-range"], [-1, "out-of-range"], [65_536, "out-of-range"]] as const) {
    const rejected = postgreSqlPersistenceConfiguration({ ...configuration, port: value as never });
    equal(rejected.ok, false);
    if (!rejected.ok) deepEqual(rejected.error, {
      code: "PLATFORM_ADAPTER_AWS_POSTGRESQL_PERSISTENCE_CONFIG_INVALID",
      defaultMessage: "PostgreSQL persistence adapter configuration is invalid.",
      details: { path: "port", reason: "Port must be an integer between 1 and 65535.", reasonCode: reason },
    });
  }
  destinationPortBinding(configuration);
  const invalid = postgreSqlPersistenceConfiguration({
    ...configuration,
    runtimeCredentialSecretReference: rejectedSecret,
  });
  equal(invalid.ok, false);
  if (!invalid.ok) equal(JSON.stringify(invalid.error).includes(rejectedSecret), false);

  const migrationDeadline = postgreSqlPersistenceConfiguration({
    ...configuration,
    statementTimeoutMs: 240_000,
  });
  equal(migrationDeadline.ok, true);
  const excessiveStatementDeadline = postgreSqlPersistenceConfiguration({
    ...configuration,
    statementTimeoutMs: 300_001,
  });
  equal(excessiveStatementDeadline.ok, false);
  if (!excessiveStatementDeadline.ok) equal(excessiveStatementDeadline.error.details.path, "statementTimeoutMs");

  equal(postgreSqlPersistenceProviderFailureClass({ code: "23505" }), "conflict");
  equal(postgreSqlPersistenceProviderFailureClass({ code: "ECONNREFUSED" }), "transport");
  deepEqual(
    postgreSqlPersistenceOperationError("claim_outbox", { code: "57014" }).params,
    { operation: "claim_outbox", provider_failure_class: "timeout" },
  );

  // An idle connection can be terminated by PostgreSQL after credential
  // revocation. The adapter must retain the server process so a later
  // readiness query can produce the governed not-ready result.
  const revokedIdlePool = new Pool({
    host: "127.0.0.1",
    port: 1,
    database: "unused",
    user: "unused",
    password: "synthetic",
  });
  nodePoolAdapter(revokedIdlePool);
  revokedIdlePool.emit("error", Object.assign(new Error("synthetic provider message"), { code: "57P01" }));
  await revokedIdlePool.end();

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
  equal(migrationQueries.some((query) => query.text === "SET LOCAL lock_timeout = '30000ms'"), true);
  equal(migrationQueries.some((query) => query.text === "SELECT pg_advisory_xact_lock(hashtext($1))"), true);
  equal(migrationQueries.some((query) => query.text.includes("tool_version")), true);

  // An ordinary migration identity owns objects in its reviewed schema, but
  // deliberately has no database-wide CREATE privilege.  Administrative
  // bootstrap therefore creates the schema first; this path must check that
  // fact rather than silently reintroduce database-wide privilege.
  const preprovisionedQueries: PostgreSqlStatement[] = [];
  const preprovisioned = await createPostgreSqlMigrationRunner(
    configuration,
    { pool: schemaPreprovisionedPool(preprovisionedQueries, true) },
    "adapter-v1",
  ).apply({ schema: configuration.schema, schemaPreprovisioned: true, migrations: [migration] });
  equal(preprovisioned.ok, true);
  equal(preprovisionedQueries.some((query) => query.text.startsWith("SELECT EXISTS (SELECT 1 FROM pg_namespace")), true);
  equal(preprovisionedQueries.some((query) => query.text.startsWith("CREATE SCHEMA")), false);
  const absentPreprovisioned = await createPostgreSqlMigrationRunner(
    configuration,
    { pool: schemaPreprovisionedPool([], false) },
    "adapter-v1",
  ).apply({ schema: configuration.schema, schemaPreprovisioned: true, migrations: [migration] });
  equal(absentPreprovisioned.ok, false);
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
  await boundaryObservations();
  await atomicObservations(configuration, { recordChange: change, outboxEntry: entry });
  await invocationDiagnostics(configuration);
  await telemetryObservations();
  await migrationObservations(configuration);
  await storeObservations(configuration, entry, change);
  await stateAndNativeObservations(configuration, entry, change);
  await reviewedCorrections(configuration);
  decodeObservations();
  console.log("PostgreSQL persistence adapter runtime test passed.");
}

function details(records: readonly DiagnosticRecord[], code: string): unknown[] { return records.filter((record) => record.code === code).map((record) => record.detail); }
function boundaryDetail(boundary: string, effect = "unknown", condition = "rejected", phase = "invocation", operation = "transaction") { return { operation, phase, boundary, condition, effect }; }
const sourceDefinition = defineDiagnostic({ code: "fixture.source", version: 1,
  classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
  detail: { type: "object", properties: { ordinal: { type: "integer", minimum: 0, maximum: 8 } } },
} as const);
const sourceRecords = Array.from({ length: 9 }, (_, ordinal) => accepted(createDiagnosticRecord(sourceDefinition, { ordinal })));
const safeSource = Object.freeze({ diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: sourceRecords.slice(1), message: "synthetic-private-observation-canary" });

async function telemetryObservations(): Promise<void> {
  type Input = Parameters<typeof recordPostgreSqlPersistenceTelemetry>[1];
  const input: Input = { operation: "write_atomic", outcome: "succeeded", durationMs: 9, error: { code: "ECONNREFUSED" }, poolInUse: 2 };
  const expected = (boundary: "encoding" | "callback", operation: Input["operation"] = "write_atomic"): DiagnosticRecord => ({
    schema: "core/diagnostic-record/v1", code: "persistence.unclassified-failure", definitionVersion: 4,
    detail: { operation, boundary, role: "primary", condition: "unclassified", codeStatus: "not-inspected", effect: "not-assessed" },
  });
  const getterOrder = ["operation", "outcome", "durationMs", "error", "error", "poolInUse", "poolInUse"];
  const unhandled: unknown[] = [];
  const onUnhandled = (cause: unknown): void => { unhandled.push(cause); };
  process.on("unhandledRejection", onUnhandled);
  try {
    for (let failedAt = 0; failedAt < getterOrder.length; failedAt++) {
      const reads: string[] = [], records: DiagnosticRecord[] = [];
      let sinkCalls = 0;
      const projected = Object.defineProperties({}, Object.fromEntries(["operation", "outcome", "durationMs", "error", "poolInUse"].map((field) => [field, {
        get() {
          reads.push(field);
          if (reads.length === failedAt + 1) throw safeSource;
          return input[field as keyof Input];
        },
      }]))) as Input;
      const binding = { diagnosticDefinitions: [sourceDefinition], onDiagnostic(this: unknown, record: DiagnosticRecord) {
        equal(this, binding); records.push(record);
      } };
      const returned: void = recordPostgreSqlPersistenceTelemetry(() => { sinkCalls++; }, projected, binding);
      equal(returned, undefined);
      equal(sinkCalls, 0);
      deepEqual(reads, getterOrder.slice(0, failedAt + 1), "projection stops at exactly the original failed getter");
      deepEqual(records, failedAt === 0 ? sourceRecords : [expected("encoding"), ...sourceRecords], "unknown operation never becomes a guessed own location");
      equal(JSON.stringify(records).includes("canary"), false);
    }
    const reads: string[] = [];
    const successfulInput = Object.defineProperties({}, Object.fromEntries(["operation", "outcome", "durationMs", "error", "poolInUse"].map((field) => [field, {
      get() { reads.push(field); return input[field as keyof Input]; },
    }]))) as Input;
    let calls = 0;
    recordPostgreSqlPersistenceTelemetry(function(this: unknown, observation) {
      equal(this, undefined); calls++;
      deepEqual(observation, { operation: "write_atomic", outcome: "succeeded", durationBucket: "under-10ms", errorClass: "transport", poolInUseBucket: "two-to-four" });
    }, successfulInput);
    equal(calls, 1); deepEqual(reads, getterOrder);
    let skippedReads = 0;
    recordPostgreSqlPersistenceTelemetry(undefined, { get operation(): Input["operation"] { skippedReads++; throw safeSource; }, outcome: "succeeded", durationMs: 0 });
    equal(skippedReads, 0, "absent sink still skips all input projection");

    let shadowReads = 0, thenableCalls = 0, thenGetterReads = 0;
    for (const [label, sink] of [
      ["frozen synchronous throw", () => { throw safeSource; }],
      ["primitive synchronous throw", () => { throw "synthetic-private-telemetry-canary"; }],
      ["native rejected promise", () => Promise.reject(safeSource)],
      ["shadowed native promise", () => Object.defineProperty(Promise.reject(safeSource), "then", { get() { shadowReads++; throw "synthetic-private-shadow-canary"; } })],
      ["rejecting thenable", () => ({ then(_resolve: unknown, reject: (cause: unknown) => void) { thenableCalls++; reject(safeSource); } })],
      ["throwing thenable", () => ({ then() { thenableCalls++; throw safeSource; } })],
      ["throwing then getter", () => Object.defineProperty({}, "then", { get() { thenGetterReads++; throw safeSource; } })],
    ] as const) {
      const records: DiagnosticRecord[] = [];
      let sinkCalls = 0;
      recordPostgreSqlPersistenceTelemetry(() => { sinkCalls++; return sink(); }, input,
        { diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => records.push(record) });
      equal(sinkCalls, 1, label);
      await new Promise<void>((resolve) => setImmediate(resolve));
      deepEqual(records, label === "primitive synchronous throw" ? [expected("callback")] : [expected("callback"), ...sourceRecords], label);
      equal(JSON.stringify(records).includes("canary"), false);
    }
    equal(shadowReads, 0); equal(thenableCalls, 2); equal(thenGetterReads, 1);
    const unselected: DiagnosticRecord[] = [];
    recordPostgreSqlPersistenceTelemetry(() => { throw safeSource; }, input, { onDiagnostic: (record) => unselected.push(record) });
    deepEqual(unselected, [expected("callback")], "unregistered fixture evidence is not trusted");
    let accessorReads = 0;
    const malformedSource = Object.defineProperty({}, "diagnosticRecord", { get() { accessorReads++; throw "synthetic-private-accessor-canary"; } });
    const malformed: DiagnosticRecord[] = [];
    recordPostgreSqlPersistenceTelemetry(() => { throw malformedSource; }, input, { onDiagnostic: (record) => malformed.push(record) });
    deepEqual(malformed, [expected("callback"), { schema: "core/diagnostic-record/v1", code: "core.diagnostics.processing-failed", definitionVersion: 1,
      detail: { reason: "evidence-inaccessible" } }]); equal(accessorReads, 0);
    for (const rejectedObserver of [() => { throw safeSource; }, () => Promise.reject(safeSource),
      () => Object.defineProperty(Promise.reject(safeSource), "then", { get() { shadowReads++; throw safeSource; } }),
      () => ({ then() { throw safeSource; } })]) {
      recordPostgreSqlPersistenceTelemetry(() => { throw safeSource; }, input, { diagnosticDefinitions: [sourceDefinition], onDiagnostic: rejectedObserver });
      recordPostgreSqlPersistenceTelemetry(() => undefined, { get operation(): Input["operation"] { throw safeSource; }, outcome: "succeeded", durationMs: 0 },
        { diagnosticDefinitions: [sourceDefinition], onDiagnostic: rejectedObserver });
    }

    for (const outcome of ["succeeded", "rolled_back", "failed"] as const) for (const asynchronous of [false, true]) {
      const sequence: string[] = [], records: DiagnosticRecord[] = [];
      const cause = Object.freeze({ code: "23505", message: "synthetic-private-transaction-canary" });
      const bodyResult = outcome === "rolled_back" ? { ok: false as const, error: "original-business-rejection" } : ok("original-value");
      const client: PostgreSqlTransactionalClient = {
        async query<TRow extends QueryResultRow>(statement: PostgreSqlStatement) { equal(this, client); sequence.push(statement.text); return queryResult<TRow>(); },
        release() { equal(this, client); sequence.push("release"); },
      };
      const pool = { ...recordingPool([]), async connect() { equal(this, pool); sequence.push("connect"); return client; } };
      let telemetryCalls = 0, telemetryReads = 0;
      let rejectTelemetry: (cause: unknown) => void = () => { throw new Error("Telemetry fixture did not receive its pending sink."); };
      const result = await withPostgreSqlTransaction<string, string>({ pool, get telemetry() {
        telemetryReads++; sequence.push("telemetry-selection");
        return function(this: unknown, observation: PostgreSqlPersistenceTelemetry) {
          equal(this, undefined); telemetryCalls++; sequence.push("sink"); equal(observation.outcome, outcome);
          if (asynchronous) return new Promise<void>((_resolve, reject) => { rejectTelemetry = reject; });
          throw safeSource;
        };
      }, diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => records.push(record) }, () => {
        sequence.push("body"); if (outcome === "failed") throw cause; return bodyResult;
      });
      equal(telemetryReads, 1); equal(telemetryCalls, 1);
      deepEqual(sequence, ["connect", "BEGIN", "body", outcome === "succeeded" ? "COMMIT" : "ROLLBACK", "telemetry-selection", "sink", "release"]);
      if (asynchronous) {
        equal(records.filter((record) => record.definitionVersion === 4).length, 0, "the transaction returns and releases without waiting for telemetry");
        rejectTelemetry(safeSource);
        await new Promise<void>((resolve) => setImmediate(resolve));
      }
      deepEqual(records.filter((record) => record.definitionVersion === 4), [expected("callback", "transaction")]);
      deepEqual(records.filter((record) => record.code === "fixture.source"), sourceRecords);
      if (outcome !== "failed") equal(result, bodyResult, "telemetry failure keeps the original Result reference");
      else { equal(result.ok, false); if (!result.ok) equal((result.error as { code: string }).code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED"); }
      deepEqual(cause, { code: "23505", message: "synthetic-private-transaction-canary" });
      equal(JSON.stringify(records).includes("canary"), false);
    }

    const observerRecords: DiagnosticRecord[] = [];
    const observer = postgreSqlPlatformPersistenceObserver(() => { throw safeSource; },
      { diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => observerRecords.push(record) });
    observer.record({ transition: "outbox.published", outcome: "succeeded" });
    deepEqual(observerRecords, [expected("callback", "transaction"), ...sourceRecords]);
    observerRecords.length = 0;
    throws(() => observer.record({ transition: "outbox.published", get outcome(): "succeeded" { throw safeSource; } }),
      (cause: unknown) => { equal(cause, safeSource); return true; });
    deepEqual(observerRecords, [expected("encoding", "transaction"), ...sourceRecords], "pre-helper projection preserves the escaping raw identity");
    for (const failedErrorRead of [1, 2]) {
      observerRecords.length = 0;
      const reads: string[] = [];
      let errorReads = 0;
      throws(() => observer.record({ transition: "outbox.published", get outcome(): "succeeded" { reads.push("outcome"); return "succeeded"; },
        get error(): unknown { reads.push("error"); if (++errorReads === failedErrorRead) throw safeSource; return safeSource; } }),
      (cause: unknown) => { equal(cause, safeSource); return true; });
      deepEqual(reads, ["outcome", ...Array(failedErrorRead).fill("error")]);
      deepEqual(observerRecords, [expected("encoding", "transaction"), ...sourceRecords]);
    }
    throws(() => postgreSqlPlatformPersistenceObserver(undefined).record({ transition: "outbox.published",
      get outcome(): "succeeded" { throw safeSource; } }), (cause: unknown) => cause === safeSource,
    "observer projection still occurs before the absent recorder sink is checked");
    if (false) {
      // @ts-expect-error Optional binding is the existing safe diagnostic contract, not raw provider detail.
      recordPostgreSqlPersistenceTelemetry(undefined, input, { sql: "unapproved" });
      // @ts-expect-error The optional observer binding does not admit provider metadata.
      postgreSqlPlatformPersistenceObserver(undefined, { rawError: safeSource });
    }
    const silenced: DiagnosticRecord[] = [];
    const unchanged = await withPostgreSqlTransaction({ pool: recordingPool([]), telemetry() { throw safeSource; }, onDiagnostic: (record) => silenced.push(record) }, () => ok(1), {});
    equal(unchanged.ok, true); equal(silenced.length, 0, "an explicit empty invocation keeps shared diagnostics silent");
    await new Promise<void>((resolve) => setImmediate(resolve));
    equal(shadowReads, 0); equal(unhandled.length, 0, "all actual rejected sink/report promises are consumed without replay or awaiting");
  } finally { process.off("unhandledRejection", onUnhandled); }
}

async function boundaryObservations(): Promise<void> {
  for (const failed of ["acquire", "begin", "body", "commit"] as const) {
    const calls: string[] = [], records: DiagnosticRecord[] = [];
    const client: PostgreSqlTransactionalClient = {
      query: async <TRow extends QueryResultRow>(statement: PostgreSqlStatement) => { calls.push(statement.text); if ((failed === "begin" && statement.text === "BEGIN") || (failed === "commit" && statement.text === "COMMIT")) throw safeSource; return queryResult<TRow>(); },
      release() { equal(this, client); calls.push("release"); },
    };
    const pool: PostgreSqlConnectionPool = { query: client.query, async connect() { equal(this, pool); calls.push("acquire"); if (failed === "acquire") throw safeSource; return client; }, end: async () => undefined };
    const result = await withPostgreSqlTransaction<string, never>({ pool, diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => records.push(record) }, () => { calls.push("body"); if (failed === "body") throw safeSource; return ok("value"); });
    equal(result.ok, false);
    if (!result.ok) { deepEqual(result.error.diagnosticRecord, sourceRecords[0]); deepEqual(result.error.relatedDiagnosticRecords, sourceRecords.slice(1)); }
    deepEqual(records.slice(0, 10), [{ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1, detail: boundaryDetail(failed, failed === "acquire" ? "not-started" : "unknown") }, ...sourceRecords]);
    equal(records.filter((record) => record.code === "fixture.source").length, 9, "transaction boundary delivery is not repeated by its error translator");
    deepEqual(calls, failed === "acquire" ? ["acquire"] : failed === "begin" ? ["acquire", "BEGIN", "release"] : failed === "body" ? ["acquire", "BEGIN", "body", "ROLLBACK", "release"] : ["acquire", "BEGIN", "body", "COMMIT", "ROLLBACK", "release"]);
    equal(JSON.stringify(records).includes("synthetic-private"), false);
  }
  const calls: string[] = [], records: DiagnosticRecord[] = [];
  const rollback = Object.freeze({ code: "ZZ999", message: "synthetic-private-rollback" });
  const recovery = Object.freeze({ code: "ZZ998", message: "synthetic-private-recovery" });
  let rollbackCount = 0;
  const client: PostgreSqlTransactionalClient = {
    query: async <TRow extends QueryResultRow>(statement: PostgreSqlStatement) => { calls.push(statement.text); if (statement.text === "ROLLBACK") throw ++rollbackCount === 1 ? rollback : recovery; return queryResult<TRow>(); },
    release: () => { calls.push("release"); },
  };
  const result = await withPostgreSqlTransaction({ pool: { ...recordingPool([]), connect: async () => client }, diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => records.push(record) }, () => ({ ok: false as const, error: safeSource }));
  equal(result.ok, false);
  deepEqual(calls, ["BEGIN", "ROLLBACK", "ROLLBACK", "release"]);
  deepEqual(details(records, "persistence.boundary-observed"), [boundaryDetail("body", "unknown", "returned-failure", "returned-result"), boundaryDetail("rollback"), boundaryDetail("recovery-rollback")]);
  deepEqual(records.slice(1, 10), sourceRecords, "body evidence precedes both rollback failures");
  const releaseCause = Object.freeze(new Error("synthetic-private-release"));
  for (const committed of [true, false]) {
    const releaseRecords: DiagnosticRecord[] = [];
    await rejects(withPostgreSqlTransaction<number, string>({ pool: { ...recordingPool([]), connect: async () => ({ query: async <TRow extends QueryResultRow>() => queryResult<TRow>(), release: () => { throw releaseCause; } }) }, onDiagnostic: (record) => releaseRecords.push(record) }, () => committed ? ok(1) : { ok: false as const, error: "original" }), (error: unknown) => error === releaseCause);
    deepEqual(details(releaseRecords, "persistence.boundary-observed").at(-1), boundaryDetail("release", committed ? "commit-completed" : "rollback-completed", "threw"));
  }
  const events = new EventEmitter() as EventEmitter & { query: () => Promise<unknown>; connect: () => Promise<unknown>; end: () => Promise<void> };
  events.query = async () => ({ rows: [] }); events.connect = async () => undefined;
  events.end = async function () { equal(this, events); throw releaseCause; };
  const poolRecords: DiagnosticRecord[] = [];
  const pool = nodePoolAdapter(events as unknown as Pool, { diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => poolRecords.push(record) });
  events.emit("error", safeSource);
  deepEqual(poolRecords.slice(1), sourceRecords);
  deepEqual(poolRecords[0]?.detail, boundaryDetail("idle-pool", "not-assessed", "rejected", "event", "connection-pool"));
  await rejects(pool.end(), (error: unknown) => error === releaseCause);
  const releaseClient = { release() { equal(this, releaseClient); throw releaseCause; } };
  throws(() => nodeClientAdapter(releaseClient as never, { onDiagnostic: (record) => poolRecords.push(record) }).release(), (error: unknown) => error === releaseCause);
  deepEqual(poolRecords.at(-1)?.detail, boundaryDetail("release", "not-assessed", "threw", "invocation", "transaction-client"));
  for (const callback of [() => { throw new Error("sink"); }, () => Promise.reject(new Error("sink"))]) {
    const primitive = await withPostgreSqlTransaction({ pool: recordingPool([]), onDiagnostic: callback }, () => { throw "private-primitive"; });
    equal(primitive.ok, false);
  }
  let accessorReads = 0;
  const unavailable = Object.defineProperty({}, "diagnosticRecord", { get() { accessorReads++; throw new Error("private"); } });
  const selected = postgreSqlPersistenceOperationError("write_atomic", unavailable, { diagnosticDefinitions: [sourceDefinition], onDiagnostic: () => undefined });
  equal(accessorReads, 0); equal(selected.diagnosticRecord?.code, "persistence.boundary-observed");
  const optionalGetter = Object.defineProperty({ pool: recordingPool([]) }, "diagnosticDefinitions", { get() { throw new Error("synthetic-private-options"); } });
  const unchanged = await withPostgreSqlTransaction<number, never>(optionalGetter, () => { throw { code: "28P01" }; });
  equal(unchanged.ok, false);
  if (!unchanged.ok) {
    equal(unchanged.error.code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED");
    equal(unchanged.error.diagnosticRecord?.code, "persistence.credential-rejected");
    equal(JSON.stringify(unchanged.error).includes("synthetic-private-options"), false);
  }
}

async function atomicObservations(configuration: PostgreSqlPersistenceConfiguration, mutation: Parameters<PlatformPersistenceTransactionScope["stage"]>[0]): Promise<void> {
  for (const [text, condition] of [[" ", "empty"], ["x".repeat(10001), "too-long"], ["INSERT x;", "semicolon"], ["INSERT x\u0000", "nul"], ["SELECT x", "unsupported-verb"]] as const) {
    const records: DiagnosticRecord[] = [], queries: PostgreSqlStatement[] = [];
    const result = await createPostgreSqlPlatformPersistenceAtomicWriter(configuration.schema, { pool: recordingPool(queries), onDiagnostic: (record) => records.push(record) }).run((scope) => stagePostgreSqlTransactionStatement(scope.transaction, { text }));
    equal(result.ok, false); if (!result.ok) deepEqual(result.error.params, { reason: "invalid_participant_statement" });
    deepEqual(details(records, "persistence.local-rejected")[0], { operation: "write_atomic", field: "statement", condition, phase: "statement-selection", effect: "local-state-unchanged" });
    deepEqual(queries.map((query) => query.text), ["BEGIN", "ROLLBACK"]);
  }
  let captured: PlatformPersistenceTransactionScope | undefined;
  const records: DiagnosticRecord[] = [];
  const writer = createPostgreSqlPlatformPersistenceAtomicWriter(configuration.schema, { pool: recordingPool([]), onDiagnostic: (record) => records.push(record) });
  await writer.run((scope) => { captured = scope; return ok(1); });
  if (captured === undefined) throw new Error("scope fixture");
  const closed = await captured.stage(mutation); equal(closed.ok, false);
  if (!closed.ok) deepEqual(closed.error.params, { reason: "closed_scope" });
  const missing = stagePostgreSqlTransactionStatement(captured.transaction, { text: "INSERT x" }); equal(missing.ok, false);
  if (!missing.ok) deepEqual(missing.error.diagnosticRecord?.detail, { operation: "write_atomic", field: "transaction", condition: "unsupported", phase: "statement-selection", effect: "local-state-unchanged" });
  const missingMutation = await writer.run((scope) => { const staged = stagePostgreSqlTransactionStatement(scope.transaction, { text: "INSERT x" }); return staged.ok ? ok(1) : staged; });
  equal(missingMutation.ok, false);
  if (!missingMutation.ok) deepEqual(missingMutation.error.params, { reason: "missing_platform_mutation" });
  const afterCommit = await writer.run<number, never>((scope) => { scope.transaction.afterCommit(() => undefined); return ok(1); });
  equal(afterCommit.ok, false);
  if (!afterCommit.ok) deepEqual(afterCommit.error.diagnosticRecord?.detail, { operation: "write_atomic", field: "after-commit", condition: "unsupported", phase: "transaction-body", effect: "local-state-unchanged" });
  equal(details(records, "persistence.local-rejected").some((detail) => (detail as { field: string }).field === "after-commit"), true);
}

async function invocationDiagnostics(configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const queries: PostgreSqlStatement[] = [], defaultsReceived: DiagnosticRecord[] = [], invocationReceived: DiagnosticRecord[] = [];
  const pool = recordingPool(queries);
  let poolReads = 0, telemetryReads = 0;
  const defaults = { get pool() { poolReads++; return pool; }, get telemetry() { telemetryReads++; return () => undefined; },
    onDiagnostic(this: unknown, record: DiagnosticRecord) { equal(this, defaults); defaultsReceived.push(record); } };
  const writer = createPostgreSqlPlatformPersistenceAtomicWriter(configuration.schema, defaults);
  const expectedLocal = { schema: "core/diagnostic-record/v1", code: "persistence.local-rejected", definitionVersion: 1,
    detail: { operation: "write_atomic", field: "participant", condition: "missing", phase: "transaction-body", effect: "local-state-unchanged" } };
  const expectedBoundary = { schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1,
    detail: boundaryDetail("body", "unknown", "returned-failure", "returned-result") };
  const defaultResult = await writer.run(() => ok(1));
  equal(defaultResult.ok, false);
  deepEqual(defaultsReceived, [expectedLocal, expectedBoundary, expectedLocal]);
  equal(poolReads, 1); equal(telemetryReads, 1);
  equal((await writer.run(() => ok(1), {})).ok, false);
  deepEqual(defaultsReceived, [expectedLocal, expectedBoundary, expectedLocal], "a supplied empty invocation silences shared defaults");
  const invocation = { onDiagnostic(this: unknown, record: DiagnosticRecord) { equal(this, invocation); invocationReceived.push(record); return Promise.reject("invocation-sink-canary"); } };
  equal((await writer.run(() => ok(1), invocation)).ok, false);
  deepEqual(invocationReceived, [expectedLocal, expectedBoundary, expectedLocal]);
  deepEqual(defaultsReceived, [expectedLocal, expectedBoundary, expectedLocal]);
  equal(poolReads, 3); equal(telemetryReads, 3);
  deepEqual(queries.map((query) => query.text), ["BEGIN", "ROLLBACK", "BEGIN", "ROLLBACK", "BEGIN", "ROLLBACK"]);
  const stagedReceived: DiagnosticRecord[] = [];
  equal((await writer.run((scope) => stagePostgreSqlTransactionStatement(scope.transaction, { text: "SELECT rejected" }), { onDiagnostic(record) { stagedReceived.push(record); } })).ok, false);
  deepEqual(stagedReceived[0], { schema: "core/diagnostic-record/v1", code: "persistence.local-rejected", definitionVersion: 1,
    detail: { operation: "write_atomic", field: "statement", condition: "unsupported-verb", phase: "statement-selection", effect: "local-state-unchanged" } });
  equal(defaultsReceived.length, 3);
  const laneDefinition = defineDiagnostic({ code: "fixture.invocation", version: 1,
    classification: { failureKind: "unknown", failureSource: "unknown", severity: "error", recovery: "manual_investigation" },
    detail: { type: "object", properties: { lane: { type: "enum", values: ["left", "right"] } } },
  } as const);
  const left = accepted(createDiagnosticRecord(laneDefinition, { lane: "left" }));
  const right = accepted(createDiagnosticRecord(laneDefinition, { lane: "right" }));
  const leftReceived: DiagnosticRecord[] = [], rightReceived: DiagnosticRecord[] = [], concurrentQueries: PostgreSqlStatement[] = [];
  const concurrent = createPostgreSqlPlatformPersistenceAtomicWriter(configuration.schema, { pool: recordingPool(concurrentQueries), diagnosticDefinitions: [laneDefinition],
    onDiagnostic() { throw new Error("Shared observer must be overridden"); } });
  let entered = 0; let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  const fail = (record: DiagnosticRecord) => async () => { entered++; if (entered === 2) release(); await gate;
    throw Object.freeze({ diagnosticRecord: record, relatedDiagnosticRecords: Array(8).fill(record), message: "private-concurrent-canary" }); };
  const results = await Promise.all([
    concurrent.run(fail(left), { onDiagnostic(record) { leftReceived.push(record); return Promise.reject("left-sink-canary"); } }),
    concurrent.run(fail(right), { onDiagnostic(record) { rightReceived.push(record); throw "right-sink-canary"; } }),
  ]);
  equal(results.every((result) => !result.ok), true);
  deepEqual(leftReceived.filter((record) => record.code === "fixture.invocation"), Array(18).fill(left));
  deepEqual(rightReceived.filter((record) => record.code === "fixture.invocation"), Array(18).fill(right));
  deepEqual(concurrentQueries.map((query) => query.text), ["BEGIN", "BEGIN", "ROLLBACK", "ROLLBACK"]);
  equal(JSON.stringify([leftReceived, rightReceived]).includes("canary"), false);
  await new Promise<void>((resolve) => setImmediate(resolve));
}

async function migrationObservations(configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const statement = { text: "CREATE TABLE fixture (id text)" };
  const migration = { id: "v0001_fixture", checksum: postgreSqlMigrationChecksum([statement]), statements: [statement] };
  const base = { schema: configuration.schema, migrations: [migration] };
  const cases = [
    { manifest: base, version: " ", field: "tool-version", condition: "pattern" },
    { manifest: { ...base, schema: "other" }, field: "schema", condition: "mismatch" },
    { manifest: { ...base, schemaPreprovisioned: "wrong" as never }, field: "schema-preprovisioned", condition: "wrong-type" },
    { manifest: { ...base, migrations: [{ ...migration, id: "BAD" }] }, field: "migration-id", condition: "pattern", ordinal: 0 },
    { manifest: { ...base, migrations: [{ ...migration, checksum: "BAD" }] }, field: "checksum", condition: "pattern", ordinal: 0 },
    { manifest: { ...base, migrations: [{ ...migration, statements: [] }] }, field: "statements", condition: "empty", ordinal: 0 },
    { manifest: { ...base, migrations: [migration, migration] }, field: "migration-id", condition: "duplicate", ordinal: 1 },
    { manifest: { ...base, migrations: [{ ...migration, id: "v0002_second" }, migration] }, field: "migration-id", condition: "out-of-order", ordinal: 1 },
    { manifest: { ...base, migrations: [{ ...migration, statements: [{ text: " " }] }] }, field: "statement", condition: "blank", ordinal: 0 },
    { manifest: { ...base, migrations: [{ ...migration, statements: [{ text: "SELECT \u0000" }] }] }, field: "statement", condition: "nul", ordinal: 0 },
  ];
  for (const fixture of cases) {
    const queries: PostgreSqlStatement[] = [], records: DiagnosticRecord[] = [];
    const runner = createPostgreSqlMigrationRunner(configuration, { pool: recordingPool(queries), onDiagnostic: (record) => records.push(record) }, fixture.version ?? "fixture-v1");
    const result = await runner.apply(fixture.manifest);
    equal(result.ok, false); deepEqual(queries, []);
    const expected = { operation: "migration", field: fixture.field, condition: fixture.condition, phase: "preflight", effect: "not-started", ...(fixture.ordinal === undefined ? {} : { ordinal: fixture.ordinal }) };
    deepEqual(records.map((record) => record.detail), [expected]);
    if (!result.ok) { equal(result.error.diagnosticRecord?.code, "persistence.local-rejected"); deepEqual(result.error.params, { operation: "migration", provider_failure_class: "unknown" }); }
  }
  const absentRecords: DiagnosticRecord[] = [];
  const absent = await createPostgreSqlMigrationRunner(configuration, { pool: schemaPreprovisionedPool([], false), onDiagnostic: (record) => absentRecords.push(record) }, "fixture-v1").apply({ ...base, schemaPreprovisioned: true });
  equal(absent.ok, false);
  deepEqual(details(absentRecords, "persistence.local-rejected")[0], { operation: "migration", field: "schema", condition: "not-found", phase: "transaction-body", effect: "unknown" });
  const queries: PostgreSqlStatement[] = [], records: DiagnosticRecord[] = [];
  let history = 0;
  const client: PostgreSqlTransactionalClient = { query: async <TRow extends QueryResultRow>(query: PostgreSqlStatement) => {
    queries.push(query); return { rows: query.text.startsWith("SELECT checksum") && ++history === 2 ? [{ checksum: "0".repeat(64) }] : [] } as unknown as QueryResult<TRow>;
  }, release: () => undefined };
  const later = await createPostgreSqlMigrationRunner(configuration, { pool: { ...recordingPool([]), connect: async () => client }, onDiagnostic: (record) => records.push(record) }, "fixture-v1").apply({ ...base, migrations: [migration, { ...migration, id: "v0002_second" }] });
  equal(later.ok, false); equal(queries.some((query) => query.text === statement.text), true); equal(queries.at(-1)?.text, "ROLLBACK");
  deepEqual(details(records, "persistence.local-rejected")[0], { operation: "migration", field: "checksum", condition: "checksum-mismatch", phase: "after-statements", effect: "unknown", ordinal: 1 });
}

function rowsPool(responses: readonly (readonly object[] | { readonly failure: unknown })[], calls: PostgreSqlStatement[]): PostgreSqlConnectionPool {
  let index = 0;
  const query = async <TRow extends QueryResultRow>(statement: PostgreSqlStatement) => {
    calls.push(statement);
    const response = responses[index++] ?? [];
    if (!Array.isArray(response)) throw (response as { readonly failure: unknown }).failure;
    return { rows: response } as unknown as QueryResult<TRow>;
  };
  return { query, connect: async () => ({ query, release: () => undefined }), end: async () => undefined };
}
const instant = new Date("2026-10-30T00:00:00.000Z");
function outboxRow(overrides: Partial<PostgreSqlOutboxRow> = {}): PostgreSqlOutboxRow {
  return { id: "fixture-outbox", subject_kind: "fixture.record", subject_id: "fixture-id", message_type: "fixture.changed", message_version: 1, delivery_policy: "fixture.delivery", created_at: instant, tenant_id: null, correlation_id: null, causation_id: null, state: "pending", attempt: 0, lease_owner: null, lease_fence: null, lease_acquired_at: null, lease_expires_at: null, published_at: null, ...overrides };
}
function processingRow(overrides: Partial<PostgreSqlProcessingRow> = {}): PostgreSqlProcessingRow {
  return { outbox_entry_id: "fixture-outbox", state: "retry-eligible", attempt: 1, lease_owner: null, lease_fence: null, lease_acquired_at: null, lease_expires_at: null, released_at: null, completion_outcome: null, completed_at: null, ...overrides };
}
function lineageRow(overrides: Partial<PostgreSqlLineageRow> = {}): PostgreSqlLineageRow {
  return { id: "fixture-change", record_kind: "fixture.record", record_id: "fixture-id", revision: 1, action: "created", occurred_at: instant, tenant_id: null, actor_kind: null, actor_id: null, correlation_id: null, causation_id: null, changed_fields: null, ...overrides };
}
async function storeObservations(configuration: PostgreSqlPersistenceConfiguration, entry: Parameters<ReturnType<typeof createPostgreSqlPlatformOutboxStore>["create"]>[0], change: Parameters<ReturnType<typeof createPostgreSqlPlatformRecordChangeStore>["append"]>[0]): Promise<void> {
  const owner = accepted(platformPersistenceLeaseOwner("fixture-owner"));
  const acquiredAt = isoDateTimeFromDate(instant);
  const lease = { lease_owner: "fixture-owner", lease_fence: 2, lease_acquired_at: instant, lease_expires_at: new Date(instant.getTime() + 1000) };
  for (const [responses, expected] of [[[outboxRow({ attempt: -1 })], "bad"], [[], "absent"]] as const) {
    const records: DiagnosticRecord[] = [], calls: PostgreSqlStatement[] = [];
    const store = createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([responses], calls), onDiagnostic: (record) => records.push(record) });
    const result = await store.create(entry); equal(result.ok, false); equal(calls.length, 1);
    const stored = details(records, "persistence.stored-record-observed") as { issues: unknown[] }[];
    deepEqual(stored[0]?.issues, expected === "absent" ? [{ field: "row", condition: "absent" }] : [{ field: "attempt", condition: "negative" }]);
  }
  for (const kind of ["outbox", "processing"] as const) {
    const records: DiagnosticRecord[] = [], calls: PostgreSqlStatement[] = [];
    const bad = kind === "outbox" ? outboxRow({ attempt: -1 }) : processingRow({ attempt: -1 });
    const options = { configuration, pool: rowsPool([[bad]], calls), onDiagnostic: (record: DiagnosticRecord) => records.push(record) };
    const result = kind === "outbox" ? await createPostgreSqlPlatformOutboxStore(options).get(entry.id) : await createPostgreSqlPlatformProcessingStore(options).get(entry.id);
    equal(result, null); equal(calls.length, 1);
    deepEqual(details(records, "persistence.stored-record-observed"), [{ operation: kind === "outbox" ? "read_outbox" : "read_processing", reduction: "null", effect: "not-assessed", issues: [{ field: "attempt", condition: "negative" }], truncated: false }]);
  }
  for (const action of ["claim", "markPublished"] as const) {
    const records: DiagnosticRecord[] = [], calls: PostgreSqlStatement[] = [];
    const store = createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([[outboxRow({ attempt: -1 })], [outboxRow({ state: "published", published_at: instant })]], calls), onDiagnostic: (record) => records.push(record) });
    const result = action === "claim" ? await store.claim({ id: entry.id, owner, acquiredAt, leaseDurationMs: 1000 }) : await store.markPublished({ id: entry.id, fence: acceptedFence(2), publishedAt: acquiredAt });
    equal(result.ok, true); equal(calls.length, 2);
    deepEqual(details(records, "persistence.local-rejected"), [], "successful duplicate reconciliation remains ordinary");
    equal(details(records, "persistence.stored-record-observed").length, 1);
  }
  for (const action of ["claim", "complete", "release"] as const) {
    const records: DiagnosticRecord[] = [], calls: PostgreSqlStatement[] = [];
    const current = action === "release" ? processingRow({ state: "claimed", ...lease }) : processingRow({ state: "completed", completion_outcome: "succeeded", completed_at: instant });
    const store = createPostgreSqlPlatformProcessingStore({ configuration, pool: rowsPool([[processingRow({ attempt: -1 })], [current]], calls), onDiagnostic: (record) => records.push(record) });
    const result = action === "claim" ? await store.claim({ outboxEntryId: entry.id, owner, acquiredAt, leaseDurationMs: 1000 }) : action === "complete" ? await store.complete({ outboxEntryId: entry.id, fence: acceptedFence(2), outcome: "succeeded", completedAt: acquiredAt }) : await store.release({ outboxEntryId: entry.id, fence: acceptedFence(2), releasedAt: acquiredAt });
    equal(calls.length, 2); equal(result.ok, action !== "release");
    const stored = details(records, "persistence.stored-record-observed") as { reduction: string }[]; equal(stored.length, 1); equal(stored[0]?.reduction, "reconciled-state");
  }
  for (const [limit, condition] of [[1.5, "not-integer"], [0, "not-positive"], [101, "too-large"]] as const) {
    const records: DiagnosticRecord[] = [], calls: PostgreSqlStatement[] = [];
    const result = await createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([], calls), onDiagnostic: (record) => records.push(record) }).listDeliverable({ asOf: acquiredAt, limit });
    equal(result.ok, false); deepEqual(calls, []);
    deepEqual(records[0]?.detail, { operation: "list_outbox", field: "limit", condition, phase: "validation", effect: "not-started" });
  }
  const records: DiagnosticRecord[] = [], calls: PostgreSqlStatement[] = [];
  const list = createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([Array.from({ length: 100 }, () => outboxRow({ attempt: -1 }))], calls), onDiagnostic: (record) => records.push(record) });
  equal((await list.listDeliverable({ asOf: acquiredAt, limit: 100 })).ok, false);
  const summary = details(records, "persistence.stored-record-observed") as { issues: unknown[] }[];
  deepEqual(summary[0]?.issues, [{ field: "attempt", condition: "negative", ordinal: 0, count: 100 }]);
  equal(summary.length, 1);
  const lineageRecords: DiagnosticRecord[] = [], lineageCalls: PostgreSqlStatement[] = [];
  const lineage = createPostgreSqlPlatformRecordChangeStore({ configuration, pool: rowsPool([[lineageRow({ revision: -1 })], [lineageRow(), lineageRow({ revision: -1 })]], lineageCalls), onDiagnostic: (record) => lineageRecords.push(record) });
  const appended = await lineage.append(change); equal(appended.ok, false); if (!appended.ok) equal(appended.error.code, "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE");
  equal((await lineage.findByRecord(change.record)).length, 1);
  deepEqual((details(lineageRecords, "persistence.stored-record-observed") as { reduction: string }[]).map((detail) => detail.reduction), ["duplicate", "filtered"]);
  const badTime = "not-a-date" as typeof acquiredAt;
  const expiryRecords: DiagnosticRecord[] = [];
  const expiryOptions = { configuration, pool: rowsPool([], []), onDiagnostic: (record: DiagnosticRecord) => expiryRecords.push(record) };
  await rejects(createPostgreSqlPlatformOutboxStore(expiryOptions).claim({ id: entry.id, owner, acquiredAt: badTime, leaseDurationMs: 1000 }), RangeError);
  const processingBad = await createPostgreSqlPlatformProcessingStore(expiryOptions).claim({ outboxEntryId: entry.id, owner, acquiredAt: badTime, leaseDurationMs: 1000 });
  equal(processingBad.ok, false);
  deepEqual(expiryRecords[0]?.detail, boundaryDetail("expiry-normalization", "not-started", "threw", "invocation", "claim_outbox"));
  const throwingCalls: PostgreSqlStatement[] = [];
  await rejects(createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([{ failure: { code: "28P01" } }], throwingCalls) }).get(entry.id), (error: unknown) => (error as { diagnosticRecord: DiagnosticRecord }).diagnosticRecord.code === "persistence.credential-rejected");
  equal(throwingCalls.length, 1);
}

function acceptedFence(value: number) { return accepted(platformPersistenceFence(value)); }

function decodeObservations(): void {
  const records: DiagnosticRecord[] = [];
  const observed = storedObservation({ onDiagnostic: (record) => records.push(record) }, "read_outbox", "null", "not-assessed");
  equal(outboxRecordFromRow(outboxRow(), observed)?.state, "pending"); observed.flush(); equal(records.length, 0, "all-null optional lease is ordinary");
  const invalidOutbox = [
    { subject_kind: "BAD" }, { subject_id: " " }, { message_type: "BAD" }, { message_version: 0 }, { delivery_policy: "BAD" },
    { attempt: 0.5 }, { attempt: -1 }, { state: "leased" as const }, { lease_owner: "fixture-owner" },
    { ...{ lease_owner: "BAD", lease_fence: 1, lease_acquired_at: instant, lease_expires_at: new Date(instant.getTime() + 1000) } },
    { lease_owner: "fixture-owner", lease_fence: 0, lease_acquired_at: instant, lease_expires_at: new Date(instant.getTime() + 1000) },
    { lease_owner: "fixture-owner", lease_fence: 1, lease_acquired_at: instant, lease_expires_at: instant },
  ];
  for (const overrides of invalidOutbox) { outboxRecordFromRow(outboxRow(overrides), observed); }
  processingRecordFromRow(processingRow({ state: "claimed" }), observed);
  processingRecordFromRow(processingRow({ completion_outcome: "succeeded" }), observed);
  for (const overrides of [{ record_kind: "BAD" }, { record_id: " " }, { revision: 0.5 }, { revision: 0 }, { actor_kind: "system" as const, actor_id: " " }, { changed_fields: ["BAD"] }, { changed_fields: ["same", "same"] }, { changed_fields: Array.from({ length: 33 }, (_, index) => `field${index}`) }]) recordChangeFromRow(lineageRow(overrides), observed);
  observed.flush();
  const bounded = records.at(-1)?.detail as { issues: unknown[]; truncated: boolean };
  equal(bounded.issues.length, 16); equal(bounded.truncated, true);
  const identifierRecords: DiagnosticRecord[] = [];
  throws(() => relation("synthetic-private-schema;", "table", { onDiagnostic: (record) => identifierRecords.push(record) }), TypeError);
  deepEqual(identifierRecords[0]?.detail, { operation: "validate-identifier", field: "identifier", condition: "pattern", phase: "preflight", effect: "not-started" });
  equal(JSON.stringify(identifierRecords).includes("synthetic-private"), false);
  const accessorCause = Object.freeze(new Error("synthetic-private-row"));
  const accessorRow = Object.defineProperty(outboxRow(), "subject_kind", { get() { throw accessorCause; } });
  const thrown = storedObservation({ onDiagnostic: () => undefined }, "read_outbox", "thrown", "not-assessed");
  throws(() => outboxRecordFromRow(accessorRow, thrown), (error: unknown) => error === accessorCause); thrown.flush();
}

async function stateAndNativeObservations(configuration: PostgreSqlPersistenceConfiguration, entry: Parameters<ReturnType<typeof createPostgreSqlPlatformOutboxStore>["create"]>[0], change: Parameters<ReturnType<typeof createPostgreSqlPlatformRecordChangeStore>["append"]>[0]): Promise<void> {
  const acquiredAt = isoDateTimeFromDate(instant), owner = accepted(platformPersistenceLeaseOwner("fixture-owner"));
  const lease = { lease_owner: "fixture-owner", lease_fence: 2, lease_acquired_at: instant, lease_expires_at: new Date(instant.getTime() + 1000) };
  for (const [row, field, condition] of [[undefined, "record", "not-found"], [outboxRow({ state: "leased", ...lease }), "fence", "stale"], [outboxRow({ state: "leased", ...lease }), "lease", "expired"]] as const) {
    const records: DiagnosticRecord[] = [], queries: PostgreSqlStatement[] = [];
    const store = createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([[], row === undefined ? [] : [row]], queries), onDiagnostic: (record) => records.push(record) });
    const result = await store.markPublished({ id: entry.id, fence: acceptedFence(condition === "stale" ? 1 : 2), publishedAt: acquiredAt });
    equal(result.ok, false); equal(queries.length, 2);
    if (condition === "expired") {
      if (!result.ok) equal(result.error.code, "PLATFORM_PERSISTENCE_LEASE_EXPIRED");
      deepEqual(details(records, "persistence.local-rejected"), []);
      deepEqual(details(records, "persistence.boundary-observed"), [{ ...boundaryDetail("reconciliation", "unknown", "returned-failure", "returned-result", "publish_outbox"), reconciliation: "lease-present-fence-matched" }]);
    } else deepEqual(details(records, "persistence.local-rejected")[0], { operation: "publish_outbox", field, condition, phase: "state-check", effect: "unknown" });
  }
  for (const action of ["complete", "release"] as const) for (const [row, field, condition] of [[undefined, "record", "not-found"], [processingRow(), "state", "wrong-state"], [processingRow({ state: "claimed", ...lease }), "fence", "stale"], [processingRow({ state: "claimed", ...lease }), "lease", "expired"]] as const) {
    const records: DiagnosticRecord[] = [], queries: PostgreSqlStatement[] = [];
    const store = createPostgreSqlPlatformProcessingStore({ configuration, pool: rowsPool([[], row === undefined ? [] : [row]], queries), onDiagnostic: (record) => records.push(record) });
    const common = { outboxEntryId: entry.id, fence: acceptedFence(condition === "stale" ? 1 : 2) };
    const result = action === "complete" ? await store.complete({ ...common, outcome: "succeeded", completedAt: acquiredAt }) : await store.release({ ...common, releasedAt: acquiredAt });
    equal(result.ok, false); equal(queries.length, 2);
    const operation = action === "complete" ? "complete_processing" : "release_processing";
    if (condition === "expired") {
      if (!result.ok) equal(result.error.code, "PLATFORM_PERSISTENCE_LEASE_EXPIRED");
      deepEqual(details(records, "persistence.local-rejected"), []);
      deepEqual(details(records, "persistence.boundary-observed"), [{ ...boundaryDetail("reconciliation", "unknown", "returned-failure", "returned-result", operation), reconciliation: "lease-present-fence-matched" }]);
    } else deepEqual(details(records, "persistence.local-rejected")[0], { operation, field, condition, phase: "state-check", effect: "unknown" });
  }
  for (const [duration, condition] of [[1.5, "not-integer"], [0, "not-positive"]] as const) {
    const records: DiagnosticRecord[] = [], queries: PostgreSqlStatement[] = [];
    const store = createPostgreSqlPlatformProcessingStore({ configuration, pool: rowsPool([], queries), onDiagnostic: (record) => records.push(record) });
    equal((await store.claim({ outboxEntryId: entry.id, owner, acquiredAt, leaseDurationMs: duration })).ok, false); equal(queries.length, 0);
    deepEqual(records[0]?.detail, { operation: "claim_processing", field: "duration", condition, phase: "validation", effect: "not-started" });
  }
  const nativeCases: readonly [string, (pool: PostgreSqlConnectionPool, diagnostics?: PlatformPersistenceDiagnosticOptions) => Promise<unknown>][] = [
    ["create_outbox", (pool, diagnostics) => createPostgreSqlPlatformOutboxStore({ configuration, pool, ...diagnostics }).create(entry)],
    ["read_outbox", (pool, diagnostics) => createPostgreSqlPlatformOutboxStore({ configuration, pool, ...diagnostics }).get(entry.id)],
    ["list_outbox", (pool, diagnostics) => createPostgreSqlPlatformOutboxStore({ configuration, pool, ...diagnostics }).listDeliverable({ asOf: acquiredAt, limit: 1 })],
    ["claim_outbox", (pool, diagnostics) => createPostgreSqlPlatformOutboxStore({ configuration, pool, ...diagnostics }).claim({ id: entry.id, owner, acquiredAt, leaseDurationMs: 1000 })],
    ["publish_outbox", (pool, diagnostics) => createPostgreSqlPlatformOutboxStore({ configuration, pool, ...diagnostics }).markPublished({ id: entry.id, fence: acceptedFence(1), publishedAt: acquiredAt })],
    ["read_processing", (pool, diagnostics) => createPostgreSqlPlatformProcessingStore({ configuration, pool, ...diagnostics }).get(entry.id)],
    ["claim_processing", (pool, diagnostics) => createPostgreSqlPlatformProcessingStore({ configuration, pool, ...diagnostics }).claim({ outboxEntryId: entry.id, owner, acquiredAt, leaseDurationMs: 1000 })],
    ["complete_processing", (pool, diagnostics) => createPostgreSqlPlatformProcessingStore({ configuration, pool, ...diagnostics }).complete({ outboxEntryId: entry.id, fence: acceptedFence(1), outcome: "succeeded", completedAt: acquiredAt })],
    ["release_processing", (pool, diagnostics) => createPostgreSqlPlatformProcessingStore({ configuration, pool, ...diagnostics }).release({ outboxEntryId: entry.id, fence: acceptedFence(1), releasedAt: acquiredAt })],
    ["append_lineage", (pool, diagnostics) => createPostgreSqlPlatformRecordChangeStore({ configuration, pool, ...diagnostics }).append(change)],
    ["read_lineage", (pool, diagnostics) => createPostgreSqlPlatformRecordChangeStore({ configuration, pool, ...diagnostics }).findByRecord(change.record)],
    ["read_lineage", (pool, diagnostics) => createPostgreSqlPlatformRecordChangeStore({ configuration, pool, ...diagnostics }).findByCause(causationId("fixture-cause"))],
  ];
  for (const [operation, run] of nativeCases) {
    const queries: PostgreSqlStatement[] = [];
    let failure: unknown;
    try { const result = await run(rowsPool([{ failure: Object.freeze({ code: "28P01", message: "synthetic-private-query" }) }], queries)); failure = (result as { error: unknown }).error; }
    catch (error) { failure = error; }
    equal(queries.length, 1);
    const error = failure as { params: unknown; diagnosticRecord: DiagnosticRecord };
    deepEqual(error.params, { operation, provider_failure_class: "access_denied" });
    equal(error.diagnosticRecord.code, "persistence.credential-rejected");
    equal(JSON.stringify(error).includes("synthetic-private"), false);
    const deliveryRecords: DiagnosticRecord[] = [], deliveryQueries: PostgreSqlStatement[] = [];
    let sourceFailure: unknown;
    try { const result = await run(rowsPool([{ failure: safeSource }], deliveryQueries), { diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => deliveryRecords.push(record) }); sourceFailure = (result as { error: unknown }).error; }
    catch (error) { sourceFailure = error; }
    equal(deliveryQueries.length, 1);
    deepEqual(deliveryRecords, [{ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1,
      detail: boundaryDetail("body", operation.startsWith("read_") || operation === "list_outbox" ? "not-assessed" : "unknown", "threw", "invocation", operation) }, ...sourceRecords], `${operation} delivers its unknown location plus source-nine without an invented provider record`);
    deepEqual((sourceFailure as { diagnosticRecord: DiagnosticRecord }).diagnosticRecord, sourceRecords[0]);
  }
  for (const kind of ["outbox", "lineage"] as const) {
    const pool = rowsPool([{ failure: { code: "23505" } }], []);
    const result = kind === "outbox" ? await createPostgreSqlPlatformOutboxStore({ configuration, pool }).create(entry) : await createPostgreSqlPlatformRecordChangeStore({ configuration, pool }).append(change);
    equal(result.ok, false); if (!result.ok) equal(result.error.code, kind === "outbox" ? "PLATFORM_PERSISTENCE_DUPLICATE_OUTBOX_ENTRY" : "PLATFORM_PERSISTENCE_DUPLICATE_RECORD_CHANGE");
  }
}

async function reviewedCorrections(configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const migration = { id: "v0001_fixture", checksum: "a".repeat(64), statements: [{ text: "SELECT 1" }] };
  for (const outer of [true, false]) for (const truthy of [true, false]) {
    const queries: PostgreSqlStatement[] = [], records: DiagnosticRecord[] = [];
    let aggregateCalls = 0, callbackCalls = 0;
    const statements = [{ text: truthy && !outer ? " " : "SELECT 1" }];
    const migrations = [{ ...migration, id: truthy && outer ? "INVALID" : migration.id, statements }];
    const items = outer ? migrations : statements;
    Object.defineProperty(items, "every", { value: (predicate: (value: unknown, ordinal: number, array: unknown[]) => unknown) => {
      aggregateCalls++;
      if (truthy) { callbackCalls++; predicate(items[0], 0, items); }
      return truthy ? "truthy custom aggregate" : 0;
    } });
    const result = await createPostgreSqlMigrationRunner(configuration, { pool: recordingPool(queries), onDiagnostic: (record) => records.push(record) }, "fixture-v1").apply({ schema: configuration.schema, migrations });
    equal(aggregateCalls, 1); equal(callbackCalls, truthy ? 1 : 0); equal(result.ok, truthy);
    if (truthy) {
      equal(queries[0]?.text, "BEGIN"); equal(queries.at(-1)?.text, "COMMIT");
      deepEqual(details(records, "persistence.local-rejected"), [], "custom truthy every overrides its callback rejection exactly as before");
    } else {
      deepEqual(queries, []);
      deepEqual(records[0]?.detail, { operation: "migration", field: outer ? "manifest" : "statements", condition: "predicate-rejected", phase: "preflight", effect: "not-started", ...(outer ? {} : { ordinal: 0 }) });
    }
  }
  for (const kind of ["outbox", "processing", "lineage"] as const) {
    const records: DiagnosticRecord[] = [];
    const operation = kind === "outbox" ? "read_outbox" : kind === "processing" ? "read_processing" : "read_lineage";
    const observed = storedObservation({ diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => records.push(record) }, operation, kind === "lineage" ? "filtered" : "null", "not-assessed");
    const date = new Date(instant); date.toISOString = () => { throw safeSource; };
    throws(() => {
      if (kind === "outbox") outboxRecordFromRow(outboxRow({ created_at: date }), observed);
      else if (kind === "processing") processingRecordFromRow(processingRow({ released_at: date }), observed);
      else recordChangeFromRow(lineageRow({ occurred_at: date }), observed);
    }, (error: unknown) => error === safeSource);
    observed.flush();
    deepEqual(records, [{ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1,
      detail: boundaryDetail("decode", "not-assessed", "threw", "invocation", operation) }, ...sourceRecords]);
    deepEqual(details(records, "persistence.stored-record-observed"), [], "an arbitrary decoder throw is not proof of invalid stored data");
  }
  const row = Object.defineProperty(outboxRow(), "subject_kind", { get() { throw safeSource; } });
  const decodedRecords: DiagnosticRecord[] = [];
  await rejects(createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([[row]], []), diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => decodedRecords.push(record) }).get(outboxEntryId("fixture-outbox")), (error: unknown) => {
    deepEqual((error as { diagnosticRecord: DiagnosticRecord }).diagnosticRecord, sourceRecords[0]);
    return true;
  });
  deepEqual(decodedRecords, [{ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1,
    detail: boundaryDetail("decode", "not-assessed", "threw", "invocation", "read_outbox") }, ...sourceRecords], "safe wrapper delivers unknown decode location and source-nine exactly once");
  const peer = { schema: "core/diagnostic-record/v1", code: "security.peer-identity-verification-failed", definitionVersion: 1, detail: { reason: "hostname-mismatch", phase: "peer-identity-verification", effect: "not-assessed" } };
  for (const withSource of [true, false]) {
    const records: DiagnosticRecord[] = [];
    const cause = Object.freeze({ ...(withSource ? safeSource : {}), code: "ERR_TLS_CERT_ALTNAME_INVALID", message: "synthetic-private-native-tls" });
    const error = postgreSqlPersistenceOperationError("read_outbox", cause, { diagnosticDefinitions: [sourceDefinition], onDiagnostic: (record) => records.push(record) });
    deepEqual(records, [{ schema: "core/diagnostic-record/v1", code: "persistence.trust-validation-failed", definitionVersion: 2,
      detail: { phase: "unknown", classification: "tls_trust_invalid", codeStatus: "recognized", operation: "read_outbox", effect: "not-assessed" } }, ...(withSource ? sourceRecords : []), peer]);
    if (withSource) deepEqual(error.relatedDiagnosticRecords, sourceRecords.slice(1), "generated peer does not displace the eighth companion");
    else deepEqual(error.relatedDiagnosticRecords, [peer]);
    equal(JSON.stringify(records).includes("synthetic-private"), false);
  }
  const retainedPeers: DiagnosticRecord[] = [];
  postgreSqlPersistenceOperationError("read_outbox", { code: "ERR_TLS_CERT_ALTNAME_INVALID", diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: [...sourceRecords.slice(1, 8), peer] },
    { diagnosticDefinitions: [sourceDefinition, ...platformSecurityDiagnosticCatalog.definitions], onDiagnostic: (record) => retainedPeers.push(record) });
  equal(retainedPeers.length, 10);
  deepEqual(retainedPeers.filter((record) => record.code === peer.code), [peer], "a generated peer already delivered in selected source evidence is not duplicated");
  for (const companionCount of [0, 7, 8]) {
    const companions = sourceRecords.slice(1, companionCount + 1);
    const error = postgreSqlPersistenceOperationError("read_outbox", { code: "ERR_TLS_CERT_ALTNAME_INVALID", diagnosticRecord: sourceRecords[0], relatedDiagnosticRecords: companions }, { diagnosticDefinitions: [sourceDefinition] });
    deepEqual(error.relatedDiagnosticRecords, companionCount < 8 ? [...companions, peer] : companions, "old callers retain generated peers in available bounded space without dropping sources");
  }
  const opaqueRecords: DiagnosticRecord[] = [], opaqueQueries: PostgreSqlStatement[] = [];
  await rejects(createPostgreSqlPlatformOutboxStore({ configuration, pool: rowsPool([{ failure: Object.freeze(new Error("synthetic-private-opaque")) }], opaqueQueries), onDiagnostic: (record) => opaqueRecords.push(record) }).get(outboxEntryId("fixture-outbox")), (error: unknown) => {
    equal((error as { code: string }).code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED");
    deepEqual((error as { diagnosticRecord: DiagnosticRecord }).diagnosticRecord, opaqueRecords[0]);
    return true;
  });
  equal(opaqueQueries.length, 1);
  deepEqual(opaqueRecords, [{ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1,
    detail: boundaryDetail("body", "not-assessed", "threw", "invocation", "read_outbox") }]);
  equal(JSON.stringify(opaqueRecords).includes("synthetic-private"), false);
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

function schemaPreprovisionedPool(queries: PostgreSqlStatement[], schemaExists: boolean): PostgreSqlConnectionPool {
  const query = async <TRow extends QueryResultRow>(statement: PostgreSqlStatement): Promise<QueryResult<TRow>> => {
    queries.push(copyStatement(statement));
    if (statement.text.startsWith("SELECT EXISTS (SELECT 1 FROM pg_namespace")) {
      return { rows: [{ exists: schemaExists }] } as unknown as QueryResult<TRow>;
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
