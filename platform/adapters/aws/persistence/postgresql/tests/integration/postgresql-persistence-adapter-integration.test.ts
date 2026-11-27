import { deepEqual, equal, rejects, ok as assertOk } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Pool, type PoolClient } from "pg";
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
  recordLifecyclePolicy,
  recordRetentionPolicyReference,
} from "@kanbien/core/persistence";
import type { Queue, QueueMessage } from "@kanbien/core/queues";
import { causationId, err, fixedClock, isoDateTimeFromDate, uuid, type ISODateTime, ok } from "@kanbien/core/shared";
import { platformJobName } from "@kanbien/platform-contracts";
import { tenantId } from "@kanbien/core/tenancy";
import {
  createPlatformOutboxRelay, createPlatformSchedule, createPlatformScheduleDelivery, createPlatformScheduleJobOutboxFactory,
  platformPersistenceDiagnosticCatalog,
  platformPersistenceError,
  platformPersistenceLeaseOwner,
  platformPersistenceMutation,
  type PlatformOutboxQueuePayload,
  type PlatformSchedule,
} from "@kanbien/platform-persistence";
import { createPlatformTestMountDeps } from "@kanbien/platform-testing";
import { createPlatformWorkerShell } from "@kanbien/platform-workers";
import { createPlatformSqsQueue, createPlatformSqsWorkerQueue, createPlatformSqsLambdaBatchHandler } from "@kanbien/platform-adapter-aws-queue-sqs";
import { archiveTestEntityService, createTestEntityService, deleteTestEntityService, entitySmokeExpiredPurgeJobName,
  purgeExpiredTestEntityService, restoreLogicallyDeletedTestEntityService, testEntityRetentionWindowMs,
  updateTestEntityService, type TestEntity, type TestEntityServiceDependencies } from "@kanbien/app-entity-smoke";
import { createEntitySmokePostgreSqlRuntime, entitySmokeMigrationManifest } from "../../../../../../../infra/04.deploy/03.product/entrypoints/entity-smoke/postgresql";
import { createEntitySmokeSchedulingApp } from "../../../../../../../infra/04.deploy/03.product/entrypoints/entity-smoke/runtime";
import { createKanbienCoreServerPostgreSqlPersistenceRuntime, kanbienCoreServerSchedulingMigrationManifest } from "../../../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-postgresql";
import { createKanbienCoreServerSchedulingApp, kanbienCoreScheduledProofJobName } from "../../../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-scheduling.app";
import { kanbienCoreSchedulingDatabasePolicy } from "../../../../../../../infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main";
import { entitySmokeSchedulingDatabasePolicy } from "../../../../../../../infra/04.deploy/03.product/entrypoints/entity-smoke/administration";
import { grantSchedulingDatabaseAccess, observeSchedulingDatabaseState, observeSchedulingMigrationPrefix, proveSchedulingDatabaseAccess } from "../../../../../../../infra/04.deploy/03.product/entrypoints/shared/persistence/scheduling-administration";
import { acceptPlatformSmokeWorkItem, platformSmokeWorkItemId } from "../../../../../../../apps/platform-smoke/src/persistence/index";
import {
  createKanbienPlatformPostgreSqlSmokePersistence,
  kanbienPlatformSmokePostgreSqlMigration,
} from "../../../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence";
import {
  createPostgreSqlMigrationRunner,
  createPostgreSqlPlatformOutboxStore,
  createPostgreSqlPlatformProcessingStore,
  createPostgreSqlPlatformScheduleStore,
  postgreSqlPersistenceConfiguration,
  postgreSqlFailureDiagnostic,
  postgreSqlMigrationChecksum,
  postgreSqlPersistenceFoundationMigration,
  postgreSqlPlatformScheduleHandoffMigration,
  postgreSqlPlatformScheduleMigration,
  postgreSqlPlatformScheduleSubjectMigration,
  postgreSqlPlatformProcessingRetryMigration,
  postgreSqlPlatformScheduleControlMigration,
  stagePostgreSqlTransactionStatement,
  type PostgreSqlPersistenceConfiguration,
} from "../../src/index";
import { nodePoolAdapter } from "../../src/connection";

const schema = "platform_smoke";
const fixtureStart = new Date("2026-09-26T12:00:00.000Z");
// Only fixed, local labels may reach the disposable-test output.  A failed
// assertion still fails closed, while CI can identify the exercised boundary
// without serialising a PostgreSQL error (which can contain connection detail).
let integrationPhase = "initialization";

async function main(): Promise<void> {
  const environment = localFixtureEnvironment();
  integrationPhase = "fixture-authentication-ready";
  await waitForFixtureAuthentication(environment);
  integrationPhase = "diagnostic-engine-failures";
  await diagnosticEngineFailures(environment);
  const rawPool = new Pool({
    host: environment.host,
    port: environment.port,
    database: environment.database,
    user: "postgres",
    password: environment.password,
    max: 2,
    connectionTimeoutMillis: 5_000,
    ssl: false,
  });

  try {
    integrationPhase = "bootstrap-ownership-repeat";
    console.log("PostgreSQL disposable assertion phase: bootstrap ownership repeat.");
    await bootstrapOwnershipRepeat(environment, rawPool);
    const pool = nodePoolAdapter(rawPool);
    const configuration = required(postgreSqlPersistenceConfiguration({
      host: environment.host,
      port: environment.port,
      database: "postgres",
      schema,
      runtimeCredentialSecretReference: "arn:aws:secretsmanager:eu-west-1:000000000000:secret:local-postgresql-fixture",
      maximumPoolSize: 2,
      connectionTimeoutMs: 5_000,
      idleTimeoutMs: 10_000,
      statementTimeoutMs: 5_000,
      tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
    }));
    const telemetry: unknown[] = [];
    const foundationMigration = postgreSqlPersistenceFoundationMigration(schema);
    const smokeMigration = kanbienPlatformSmokePostgreSqlMigration(schema);
    const scheduleMigration = postgreSqlPlatformScheduleMigration(schema, "v0003_platform_schedule");
    const scheduleHandoffMigration = postgreSqlPlatformScheduleHandoffMigration(schema, "v0004_platform_schedule_handoff");
    const migrations = [foundationMigration, smokeMigration, scheduleMigration, scheduleHandoffMigration,
      postgreSqlPlatformScheduleSubjectMigration(schema, "v0005_platform_schedule_subject"),
      postgreSqlPlatformProcessingRetryMigration(schema, "v0006_platform_processing_retry"),
      postgreSqlPlatformScheduleControlMigration(schema, "v0007_platform_schedule_control")];
    const migrationRunner = createPostgreSqlMigrationRunner(configuration, { pool }, "stage3-local");
    integrationPhase = "immutable-migrations";
    console.log("PostgreSQL disposable assertion phase: immutable migrations.");
    equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_namespace WHERE nspname = $1", [schema]), 0,
      "The transition-fault fixture may only use a previously absent disposable schema.");
    const applied = await migrationRunner.apply({ schema, migrations });
    equal(applied.ok, true, "The immutable migration manifest must apply to the disposable engine.");

    const changedChecksum = await migrationRunner.apply({
      schema,
      migrations: [foundationMigration, { ...smokeMigration, checksum: "f".repeat(64) }],
    });
    equal(changedChecksum.ok, false, "A changed checksum for an applied migration must fail closed.");
    if (!changedChecksum.ok) {
      equal(changedChecksum.error.code, "PLATFORM_PERSISTENCE_MIGRATION_CHECKSUM_MISMATCH");
    }
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_migration_history"`), migrations.length);

    integrationPhase = "schedule-storage";
    console.log("PostgreSQL disposable assertion phase: schedule storage.");
    const schedule = required(createPlatformSchedule({
      jobName: required(platformJobName("entity-smoke.test-entity.purge-expired")), dueAt: "2026-09-23T13:30:00+01:00",
      subject: recordReference({ kind: required(recordKind("fixture.test-entity")), id: required(recordId("owned-entity")) }),
    }, { generate: () => uuid("e1d06aac-3d17-4292-b9f3-1fe370772a5d") }));
    const scheduleStore = createPostgreSqlPlatformScheduleStore({ configuration, pool });
    const createdSchedule = await scheduleStore.create(schedule);
    equal(createdSchedule.ok, true);
    deepEqual(await scheduleStore.get(schedule.id), schedule);
    equal(required(await scheduleStore.blockDue({ scheduleId: schedule.id, asOf: schedule.dueAt })).state, "blocked-job-unavailable");
    equal(required(await scheduleStore.listDue({ asOf: schedule.dueAt, limit: 100 })).length, 0);
    equal(required(await scheduleStore.resumeBlocked(schedule.id)).state, "waiting");
    const scheduleOutbox = outboxEntry({ id: outboxEntryId("schedule-handoff-proof"),
      subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(String(schedule.id))) }),
      messageType: required(outboxMessageType("platform.schedule.due")),
      deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")), createdAt: schedule.dueAt });
    const handoff = await scheduleStore.handoverDue({ scheduleId: schedule.id, asOf: schedule.dueAt, outboxEntry: scheduleOutbox });
    equal(handoff.ok, true);
    if (!handoff.ok || handoff.value.disposition !== "outbox-created") throw new Error("Expected schedule handoff to create one outbox record.");
    equal(handoff.value.schedule.outboxEntryId, scheduleOutbox.id);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE id = 'schedule-handoff-proof'`), 1);
    // Only the two exact records owned by this phase are removed. Subsequent
    // existing phases assert their own complete fact counts in this schema.
    await rawPool.query({ text: `DELETE FROM "${schema}"."platform_schedule" WHERE id = $1`, values: [schedule.id] });
    await rawPool.query({ text: `DELETE FROM "${schema}"."platform_outbox" WHERE id = $1`, values: [scheduleOutbox.id] });
    integrationPhase = "schedule-engine-concurrency-and-repair";
    await scheduleEngineSafety(rawPool, configuration);
    integrationPhase = "schedule-schema-isolation";
    await scheduleSchemaIsolation(rawPool, configuration);
    integrationPhase = "entity-reminder-atomicity-and-targeted-purge";
    await entityReminderEngineSafety(rawPool, configuration);
    integrationPhase = "independent-baseline-scheduled-acceptance";
    await baselineSchedulingEngineSafety(rawPool, configuration);

    integrationPhase = "least-privilege-roles";
    console.log("PostgreSQL disposable assertion phase: least-privilege migration and runtime roles.");
    await rawPool.query({ text: "DO $$ BEGIN CREATE ROLE psmokemigrate LOGIN PASSWORD 'fixture-migration-password'; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await rawPool.query({ text: "DO $$ BEGIN CREATE ROLE psmokeruntime LOGIN PASSWORD 'fixture-runtime-password'; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await rawPool.query({ text: `ALTER SCHEMA "${schema}" OWNER TO psmokemigrate` });
    await rawPool.query({ text: `GRANT CONNECT ON DATABASE postgres TO psmokeruntime; GRANT USAGE ON SCHEMA "${schema}" TO psmokeruntime; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA "${schema}" TO psmokeruntime` });
    await rawPool.query({ text: `SET ROLE psmokemigrate; ALTER DEFAULT PRIVILEGES IN SCHEMA "${schema}" GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO psmokeruntime; RESET ROLE` });
    const runtimePool = new Pool({
      host: environment.host,
      port: environment.port,
      database: environment.database,
      user: "psmokeruntime",
      password: "fixture-runtime-password",
      max: 1,
      connectionTimeoutMillis: 5_000,
      ssl: false,
    });
    try {
      await runtimePool.query({ text: `INSERT INTO "${schema}"."platform_smoke_work_item" (id, state, revision, accepted_at) VALUES ($1, 'accepted', 1, CURRENT_TIMESTAMP)`, values: ["runtime-dml-proof"] });
      await runtimePool.query({ text: `DELETE FROM "${schema}"."platform_smoke_work_item" WHERE id = $1`, values: ["runtime-dml-proof"] });
      let ddlRejected = false;
      try {
        await runtimePool.query({ text: `CREATE TABLE "${schema}"."runtime_ddl_must_fail" (id text)` });
      } catch {
        ddlRejected = true;
      }
      equal(ddlRejected, true, "The runtime role must retain DML access while being unable to create schema objects.");
    } finally {
      await runtimePool.end();
    }

    integrationPhase = "bootstrap-effects-reconciliation";
    console.log("PostgreSQL disposable assertion phase: bootstrap-effect read-only reconciliation.");
    await bootstrapEffectsReadOnlyReconciliation(environment, rawPool);

    const smokePersistence = createKanbienPlatformPostgreSqlSmokePersistence({
      configuration,
      pool,
      telemetry: (observation) => telemetry.push(observation),
    });
    const atomicWorkItemId = required(platformSmokeWorkItemId("synthetic-work-item-atomic"));
    integrationPhase = "atomic-state-lineage-outbox";
    console.log("PostgreSQL disposable assertion phase: atomic state, lineage, and outbox.");
    const accepted = await acceptPlatformSmokeWorkItem({
      id: atomicWorkItemId,
      acceptedAt: at(0),
      causationId: causationId("synthetic-cause-atomic"),
    }, smokePersistence);
    equal(accepted.ok, true, "The smoke capability must atomically write state, lineage, and an outbox obligation.");
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_smoke_work_item"`), 1);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_record_change"`), 1);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox"`), 1);

    const rollbackId = "synthetic-work-item-rollback";
    integrationPhase = "atomic-rollback";
    console.log("PostgreSQL disposable assertion phase: atomic rollback.");
    const rollback = await smokePersistence.atomicWriter.run(async (scope) => {
      const participant = stagePostgreSqlTransactionStatement(scope.transaction, {
        text: `INSERT INTO "${schema}"."platform_smoke_work_item" (id, state, revision, accepted_at) VALUES ($1, 'accepted', 1, $2)`,
        values: [rollbackId, at(1)],
      });
      if (!participant.ok) return participant;
      const staged = await scope.stage(testMutation(rollbackId, at(1), "synthetic-tenant-a"));
      if (!staged.ok) return staged;
      return err(platformPersistenceError({
        code: "PLATFORM_PERSISTENCE_INVALID_MUTATION",
        defaultMessage: "The disposable fixture intentionally rolls this transaction back.",
        messageKey: "platform.persistence.fixture.rollback",
      }));
    });
    equal(rollback.ok, false, "A failed atomic operation must roll all participants back.");
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_smoke_work_item" WHERE id = $1`, [rollbackId]), 0);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_record_change" WHERE record_id = $1`, [rollbackId]), 0);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE subject_id = $1`, [rollbackId]), 0);

    integrationPhase = "optimistic-concurrency";
    console.log("PostgreSQL disposable assertion phase: optimistic concurrency.");
    const updated = await rawPool.query({
      text: `UPDATE "${schema}"."platform_smoke_work_item" SET revision = $1 WHERE id = $2 AND revision = $3 RETURNING revision`,
      values: [2, String(atomicWorkItemId), 1],
    });
    equal(updated.rowCount, 1, "The current revision must permit one update.");
    const stale = await rawPool.query({
      text: `UPDATE "${schema}"."platform_smoke_work_item" SET revision = $1 WHERE id = $2 AND revision = $3 RETURNING revision`,
      values: [3, String(atomicWorkItemId), 1],
    });
    equal(stale.rowCount, 0, "A stale optimistic-concurrency revision must update no record.");

    integrationPhase = "tenant-predicate-isolation";
    console.log("PostgreSQL disposable assertion phase: tenant predicate isolation.");
    await rawPool.query({
      text: `CREATE TABLE "${schema}"."synthetic_tenant_item" (tenant_id text NOT NULL, id text NOT NULL, state text NOT NULL, PRIMARY KEY (tenant_id, id))`,
    });
    await rawPool.query({
      text: `INSERT INTO "${schema}"."synthetic_tenant_item" (tenant_id, id, state) VALUES ($1, $2, 'accepted')`,
      values: ["synthetic-tenant-a", "synthetic-tenant-record"],
    });
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."synthetic_tenant_item" WHERE tenant_id = $1 AND id = $2`, ["synthetic-tenant-b", "synthetic-tenant-record"]), 0);
    equal((await rawPool.query({
      text: `UPDATE "${schema}"."synthetic_tenant_item" SET state = 'updated' WHERE tenant_id = $1 AND id = $2`,
      values: ["synthetic-tenant-b", "synthetic-tenant-record"],
    })).rowCount, 0);
    equal((await rawPool.query({
      text: `DELETE FROM "${schema}"."synthetic_tenant_item" WHERE tenant_id = $1 AND id = $2`,
      values: ["synthetic-tenant-b", "synthetic-tenant-record"],
    })).rowCount, 0);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."synthetic_tenant_item" WHERE tenant_id = $1 AND id = $2`, ["synthetic-tenant-a", "synthetic-tenant-record"]), 1);

    integrationPhase = "outbox-lease-fencing";
    console.log("PostgreSQL disposable assertion phase: outbox lease fencing.");
    const outbox = createPostgreSqlPlatformOutboxStore({ configuration, pool });
    const fencedEntry = testMutation("synthetic-fenced-record", at(4), "synthetic-tenant-a").outboxEntry;
    equal((await outbox.create(fencedEntry)).ok, true);
    const ownerOne = required(platformPersistenceLeaseOwner("fixture-owner-one"));
    const ownerTwo = required(platformPersistenceLeaseOwner("fixture-owner-two"));
    const firstClaim = await outbox.claim({ id: fencedEntry.id, owner: ownerOne, acquiredAt: at(4), leaseDurationMs: 1_000 });
    equal(firstClaim.ok, true);
    const firstFence = claimedFence(firstClaim);
    const secondClaim = await outbox.claim({ id: fencedEntry.id, owner: ownerTwo, acquiredAt: at(6), leaseDurationMs: 1_000 });
    equal(secondClaim.ok, true);
    const secondFence = claimedFence(secondClaim);
    equal(Number(secondFence) > Number(firstFence), true, "A later claimant must receive a higher fence.");
    const staleCompletion = await outbox.markPublished({ id: fencedEntry.id, fence: firstFence, publishedAt: at(6.5) });
    equal(staleCompletion.ok, false, "An expired claimant must not publish behind a newer fence.");
    if (!staleCompletion.ok) equal(staleCompletion.error.code, "PLATFORM_PERSISTENCE_STALE_FENCE");
    equal((await outbox.markPublished({ id: fencedEntry.id, fence: secondFence, publishedAt: at(6.5) })).ok, true);

    integrationPhase = "relay-ordering";
    console.log("PostgreSQL disposable assertion phase: relay ordering.");
    const relayEntry = testMutation("synthetic-relay-record", at(-1), "synthetic-tenant-a").outboxEntry;
    equal((await outbox.create(relayEntry)).ok, true);
    const queue = inMemoryQueue();
    const relay = createPlatformOutboxRelay({
      outbox,
      queue,
      owner: ownerOne,
      leaseDurationMs: 1_000,
      clock: { now: () => new Date(fixtureStart.getTime() + 8_000) },
    });
    const relayed = await relay.runOnce();
    equal(relayed.ok, true);
    if (relayed.ok) equal(relayed.value.status, "published", "The local relay must send before it marks the outbox entry published.");
    equal(queue.messages.length, 1, "The relay must emit only one minimal queue envelope.");
    equal((await outbox.get(relayEntry.id))?.state, "published");

    integrationPhase = "worker-processing-fence";
    console.log("PostgreSQL disposable assertion phase: worker processing fence.");
    const processing = createPostgreSqlPlatformProcessingStore({ configuration, pool });
    const processingFirstClaim = await processing.claim({ outboxEntryId: relayEntry.id, owner: ownerOne, acquiredAt: at(10), leaseDurationMs: 1_000 });
    equal(processingFirstClaim.ok, true);
    const processingFirstFence = claimedFence(processingFirstClaim);
    const processingSecondClaim = await processing.claim({ outboxEntryId: relayEntry.id, owner: ownerTwo, acquiredAt: at(12), leaseDurationMs: 1_000 });
    equal(processingSecondClaim.ok, true);
    const processingSecondFence = claimedFence(processingSecondClaim);
    const staleWorker = await processing.complete({ outboxEntryId: relayEntry.id, fence: processingFirstFence, outcome: "succeeded", completedAt: at(12.5) });
    equal(staleWorker.ok, false, "A stale worker must not complete behind the newest processing fence.");
    if (!staleWorker.ok) equal(staleWorker.error.code, "PLATFORM_PERSISTENCE_STALE_FENCE");
    equal((await processing.complete({ outboxEntryId: relayEntry.id, fence: processingSecondFence, outcome: "succeeded", completedAt: at(12.5) })).ok, true);

    integrationPhase = "processing-durable-retry-time";
    const retryEntry = testMutation("synthetic-retry-time-record", at(20), "synthetic-tenant-a").outboxEntry;
    required(await outbox.create(retryEntry));
    const retryClaim = await processing.claim({ outboxEntryId: retryEntry.id, owner: ownerOne, acquiredAt: at(20), leaseDurationMs: 20_000 });
    required(await processing.release({ outboxEntryId: retryEntry.id, fence: claimedFence(retryClaim), releasedAt: at(21), retryAt: at(30) }));
    const reconstructedProcessing = createPostgreSqlPlatformProcessingStore({ configuration, pool });
    equal((await reconstructedProcessing.get(retryEntry.id))?.retryAt, at(30), "Retry time survives reconstruction from persisted state.");
    equal(required(await reconstructedProcessing.claim({ outboxEntryId: retryEntry.id, owner: ownerTwo, acquiredAt: at(29.999), leaseDurationMs: 1_000 })).disposition, "retry-not-due");
    const retryDue = await reconstructedProcessing.claim({ outboxEntryId: retryEntry.id, owner: ownerTwo, acquiredAt: at(30), leaseDurationMs: 1_000 });
    equal(required(retryDue).disposition, "claimed");
    assertOk(Number(claimedFence(retryDue)) > Number(claimedFence(retryClaim)));
    equal(required(retryDue).record.retryAt, undefined);

    integrationPhase = "migration-continuation";
    console.log("PostgreSQL disposable assertion phase: locked migration continuation.");
    await migrationContinuationEngineSafety(rawPool, configuration);
    integrationPhase = "scheduling-effective-identities";
    console.log("PostgreSQL disposable assertion phase: independently authenticated scheduling identities.");
    await schedulingEffectiveIdentityProof(rawPool, environment);

    integrationPhase = "telemetry-safety";
    console.log("PostgreSQL disposable assertion phase: telemetry safety.");
    const telemetryText = JSON.stringify(telemetry);
    equal(telemetryText.includes(environment.password), false, "Normal telemetry must not contain the fixture password.");
    equal(telemetryText.includes("synthetic-tenant-a"), false, "Normal telemetry must not contain a tenant identifier.");
    console.log("PostgreSQL disposable integration proof passed.");
  } finally {
    await rawPool.end();
  }
}

async function measureSchedulingWorkload(rawPool: Pool, scope: "core-server-persistence" | "entity-smoke",
  operation: (index: number) => Promise<void>): Promise<void> {
  const namespace = scope === "core-server-persistence" ? "platform" : "entity_smoke";
  const tables = ["platform_schedule", "platform_outbox", "platform_processing",
    scope === "core-server-persistence" ? "core_server_persistence_acceptance" : "test_entity"];
  const retained = async () => {
    let total = 0;
    for (const table of tables) {
      const result = await rawPool.query<{ bytes: string }>({ text: "SELECT pg_total_relation_size($1::regclass)::text AS bytes",
        values: [`${namespace}.${table}`] });
      total += Number(result.rows[0]?.bytes);
    }
    assertOk(Number.isSafeInteger(total) && total > 0);
    return total;
  };
  const engine = (await rawPool.query<{ version: number; block_size: number; full_page_writes: string }>({
    text: "SELECT current_setting('server_version_num')::integer AS version, current_setting('block_size')::integer AS block_size, current_setting('full_page_writes') AS full_page_writes",
  })).rows[0]!;
  equal(engine.block_size, 8192); equal(engine.full_page_writes, "on");
  const before = await retained();
  const beginning = (await rawPool.query<{ lsn: string }>({ text: "SELECT pg_current_wal_insert_lsn()::text AS lsn" })).rows[0]!.lsn;
  const occurrences = 128;
  for (let index = 0; index < occurrences; index++) await operation(index);
  const retainedBytes = (await retained()) - before;
  const written = await rawPool.query<{ bytes: string }>({
    text: "SELECT pg_wal_lsn_diff(pg_current_wal_insert_lsn(), $1::pg_lsn)::text AS bytes", values: [beginning],
  });
  const walBytes = Number(written.rows[0]?.bytes);
  assertOk(Number.isSafeInteger(retainedBytes) && retainedBytes > 0 && Number.isSafeInteger(walBytes) && walBytes > 0);
  // These are measured engineering allowances, not universal PostgreSQL or
  // workload bounds. Include indexes, TOAST and dead tuples before vacuum;
  // instance-wide WAL can include background activity, conservatively.
  assertOk(retainedBytes <= occurrences * 8192, "Declared fixed jobs must fit the reviewed 8KiB retained-byte allowance.");
  assertOk(walBytes <= occurrences * 262144, "Declared fixed jobs must fit the reviewed 256KiB WAL allowance.");
}

async function migrationContinuationEngineSafety(rawPool: Pool, configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const scope = "scheduler_continuation";
  equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_namespace WHERE nspname=$1", [scope]), 0);
  const migrations = [1, 2, 3].map(ordinal => {
    const statements = [{ text: `CREATE TABLE "${scope}".fixture_${ordinal} (id integer PRIMARY KEY)` }];
    return { id: `v000${ordinal}_continuation_fixture`, statements, checksum: postgreSqlMigrationChecksum(statements) };
  });
  const runner = createPostgreSqlMigrationRunner({ ...configuration, schema: scope }, { pool: nodePoolAdapter(rawPool) }, "continuation-fixture");
  const manifest = { schema: scope, migrations, continuation: { minimumAppliedMigrations: 1 } };
  const identity = await rawPool.query<{ username: string }>({ text: "SELECT current_user AS username" });
  const prefixPolicy = { ...kanbienCoreSchedulingDatabasePolicy(configuration.database, identity.rows[0]!.username, "prefix_http_fixture"), manifest };
  const observePrefix = () => observeSchedulingMigrationPrefix(nodePoolAdapter(rawPool), prefixPolicy);
  try {
    equal((await runner.apply(manifest)).ok, false, "Continuation cannot create an absent historical scope.");
    equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_namespace WHERE nspname=$1", [scope]), 0);
    required(await runner.apply({ schema: scope, migrations: migrations.slice(0, 1) }));
    const firstPrefix = await observePrefix();
    equal(firstPrefix.state, "partial"); equal(firstPrefix.applied_migrations, 1); equal(firstPrefix.minimum_applied_migrations, 1);
    equal(firstPrefix.manifest_migration_count, 3);
    equal(firstPrefix.manifest_sha256 === firstPrefix.applied_prefix_sha256, false);
    equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=$1 AND c.relname IN ('platform_schedule','platform_outbox','platform_processing')", [scope]), 0,
      "An accepted partial journal can be observed before any scheduler table exists.");
    for (const changed of ["unknown", "checksum"] as const) {
      if (changed === "unknown") await rawPool.query({ text: `UPDATE "${scope}".platform_migration_history SET migration_id='v9999_unknown'` });
      else await rawPool.query({ text: `UPDATE "${scope}".platform_migration_history SET checksum=$1`, values: ["f".repeat(64)] });
      equal((await runner.apply(manifest)).ok, false);
      await rejects(observePrefix, "Observation must reject the same damaged journal as the mutation runner.");
      equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=$1 AND c.relname='fixture_2'", [scope]), 0);
      await rawPool.query({ text: `UPDATE "${scope}".platform_migration_history SET migration_id=$1, checksum=$2`, values: [migrations[0]!.id, migrations[0]!.checksum] });
    }
    // Another actor changes the journal while the runner waits for the same
    // migration lock. The continuation must inspect the post-lock history.
    const blocker = await rawPool.connect();
    let pending: ReturnType<typeof runner.apply> | undefined;
    let pendingPrefix: Promise<string> | undefined;
    try {
      await blocker.query("BEGIN");
      await blocker.query({ text: "SELECT pg_advisory_xact_lock(hashtext($1))", values: [`kanbien-postgresql-migration:${scope}`] });
      pendingPrefix = observePrefix().then(() => "accepted", () => "rejected");
      let timer: ReturnType<typeof setTimeout> | undefined;
      try {
        equal(await Promise.race([pendingPrefix, new Promise(resolve => { timer = setTimeout(() => resolve("timed-out"), 2000); })]), "rejected", "A prefix observer must reject while the competing migration still holds its lock.");
      } finally { if (timer !== undefined) clearTimeout(timer); }
      pending = runner.apply(manifest);
      await blocker.query({ text: `UPDATE "${scope}".platform_migration_history SET checksum=$1`, values: ["f".repeat(64)] });
      await blocker.query("COMMIT");
      equal((await pending).ok, false, "A changed journal cannot rely on an earlier prefix observation.");
    } finally { try { await blocker.query("ROLLBACK"); } finally { blocker.release(); await pendingPrefix; } }
    await rawPool.query({ text: `UPDATE "${scope}".platform_migration_history SET checksum=$1`, values: [migrations[0]!.checksum] });
    required(await runner.apply({ ...manifest, migrations: migrations.slice(0, 2) }));
    const secondPrefix = await observePrefix();
    equal(secondPrefix.applied_migrations, 2); equal(secondPrefix.state, "partial");
    equal(secondPrefix.manifest_sha256, firstPrefix.manifest_sha256); equal(secondPrefix.applied_prefix_sha256 === firstPrefix.applied_prefix_sha256, false);
    const resumed = await Promise.all([runner.apply(manifest), runner.apply(manifest)]);
    equal(resumed.every(result => result.ok), true);
    equal(resumed.flatMap(result => required(result)).filter(result => result.status === "applied").length, 1);
    const reconciled = required(await runner.apply(manifest));
    equal(reconciled.every(result => result.status === "already-applied"), true, "A lost successful response is reconciled without replaying DDL.");
    const completePrefix = await observePrefix();
    equal(completePrefix.state, "complete"); equal(completePrefix.applied_migrations, 3);
    equal(completePrefix.applied_prefix_sha256, completePrefix.manifest_sha256);
    await rawPool.query({ text: `DELETE FROM "${scope}".platform_migration_history WHERE migration_id=$1`, values: [migrations[1]!.id] });
    equal((await runner.apply(manifest)).ok, false, "A missing middle record is not a resumable suffix.");
    await rejects(observePrefix, "A missing middle record cannot be reported as a partial prefix.");
  } finally { await rawPool.query({ text: `DROP SCHEMA IF EXISTS "${scope}" CASCADE` }); }
}

async function schedulingEffectiveIdentityProof(rawPool: Pool, environment: ReturnType<typeof localFixtureEnvironment>): Promise<void> {
  const policies = [kanbienCoreSchedulingDatabasePolicy(environment.database, "core_migration_fixture", "core_http_fixture"), entitySmokeSchedulingDatabasePolicy(environment.database)];
  const allRoles = policies.flatMap(policy => [policy.migrationUsername, policy.httpUsername, policy.dispatchUsername, policy.workerUsername]);
  equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_roles WHERE rolname=ANY($1::text[])", [allRoles]), 0, "Effective-role proof only creates initially absent disposable identities.");
  equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_roles WHERE rolname='rds_iam'"), 0);
  await rawPool.query({ text: "CREATE ROLE rds_iam NOLOGIN" }); // Membership semantics only, not an RDS IAM authentication claim.
  for (const policy of policies) {
    const scope = policy.manifest.schema;
    await rawPool.query({ text: `INSERT INTO "${scope}".platform_schedule (id,job_name,due_at,state) VALUES ('79999999-1111-4111-8111-111111111111','fixture.future-unknown-work','2099-01-01T00:00:00Z','waiting')` });
    await rawPool.query({ text: `INSERT INTO "${scope}".platform_outbox (id,subject_kind,subject_id,message_type,message_version,delivery_policy,created_at,state,attempt,lease_expires_at) VALUES ('inventory-future-work','fixture.unknown','inventory-future-work','fixture.unknown',1,'at-least-once',CURRENT_TIMESTAMP,'leased',1,'2099-01-01T00:00:00Z')` });
    await rawPool.query({ text: `INSERT INTO "${scope}".platform_processing (outbox_entry_id,state,attempt,released_at,retry_at) VALUES ('inventory-future-work','retry-eligible',1,CURRENT_TIMESTAMP,'2099-01-01T00:00:00Z')` });
  }
  const snapshot = async () => {
    const rows: string[] = [];
    for (const policy of policies) for (const table of [policy.applicationTable, "platform_schedule", "platform_outbox", "platform_processing", "platform_migration_history"]) {
      const result = await rawPool.query<{ snapshot: string }>({ text: `SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text), '[]'::jsonb)::text AS snapshot FROM "${policy.manifest.schema}"."${table}" t` });
      rows.push(result.rows[0]!.snapshot);
    }
    return rows;
  };
  const original = await snapshot();
  const admin = nodePoolAdapter(rawPool);
  for (const policy of policies) {
    for (const username of [policy.migrationUsername, policy.httpUsername]) {
      await rawPool.query({ text: `CREATE ROLE "${username}" LOGIN NOINHERIT PASSWORD 'synthetic-scheduling-role-proof'` });
    }
    await rawPool.query({ text: `ALTER SCHEMA "${policy.manifest.schema}" OWNER TO "${policy.migrationUsername}"` });
    for (const table of [policy.applicationTable, "platform_schedule", "platform_outbox", "platform_processing", "platform_record_change", "platform_migration_history"]) {
      await rawPool.query({ text: `ALTER TABLE "${policy.manifest.schema}"."${table}" OWNER TO "${policy.migrationUsername}"` });
    }
    // The observer must refuse a busy migration lock before reading any state.
    // Waiting here would freeze its repeatable-read snapshot before the wait.
    const blocker = await rawPool.connect(), statements: string[] = [], conditions: unknown[] = [];
    let pendingObservation: Promise<"accepted" | "rejected"> | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      await blocker.query("BEGIN");
      await blocker.query({ text: "SELECT pg_advisory_xact_lock(hashtext($1))", values: [`kanbien-postgresql-migration:${policy.manifest.schema}`] });
      const trackedPool: ReturnType<typeof nodePoolAdapter> = {
        query: statement => admin.query(statement), end: () => admin.end(),
        async connect() {
          const client = await admin.connect();
          return { query: statement => { statements.push(statement.text); return client.query(statement); }, release: () => client.release() };
        },
      };
      pendingObservation = observeSchedulingDatabaseState(trackedPool, policy, { onObservation(record) {
        const detail = record.detail as { operation?: unknown; field?: unknown; condition?: unknown };
        if (detail.operation === "migration-state" && detail.field === "row") conditions.push(detail.condition);
      } }).then(() => "accepted" as const, () => "rejected" as const);
      const result = await Promise.race([pendingObservation, new Promise<"timed-out">((resolve) => { timer = setTimeout(() => resolve("timed-out"), 2000); })]);
      equal(result, "rejected", "A contended observer must settle while the matching migration lock remains held.");
      deepEqual(conditions, ["not-true"]);
      deepEqual(statements, ["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY", "SET LOCAL lock_timeout = '30000ms'", "SELECT pg_try_advisory_xact_lock(hashtext($1)) AS acquired", "ROLLBACK"], "A busy observer must not read history, schema state or work inventory.");
    } finally {
      if (timer !== undefined) clearTimeout(timer);
      try { await blocker.query("ROLLBACK"); }
      finally { blocker.release(); await pendingObservation; }
    }
    // This is a new invocation after release, not replay of a pre-wait view.
    const observed = await observeSchedulingDatabaseState(admin, policy);
    const prefix = await observeSchedulingMigrationPrefix(admin, policy);
    equal(prefix.state, "complete"); equal(prefix.applied_migrations, 7);
    equal(prefix.minimum_applied_migrations, policy.manifest.schema === "platform" ? 2 : 1);
    equal(prefix.manifest_sha256, observed.manifest_sha256); equal(prefix.applied_prefix_sha256, prefix.manifest_sha256);
    const { work_inventory: inventory, ...manifestIdentity } = observed;
    equal(inventory.waiting_schedules, await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${policy.manifest.schema}".platform_schedule WHERE state='waiting'`));
    equal(inventory.pending_outbox, await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${policy.manifest.schema}".platform_outbox WHERE state IN ('pending','leased')`));
    equal(inventory.active_processing, await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${policy.manifest.schema}".platform_processing WHERE state IN ('claimed','retry-eligible')`));
    equal(Object.values(inventory).every(value => Number.isSafeInteger(value) && value >= 1), true, "Unknown future schedules, leased outbox and future processing retries all block an empty-before-proof activation decision.");
    const granted = await grantSchedulingDatabaseAccess(admin, policy);
    deepEqual(granted, observed);
    for (const username of [policy.dispatchUsername, policy.workerUsername]) {
      await rawPool.query({ text: `ALTER ROLE "${username}" PASSWORD 'synthetic-scheduling-role-proof'` });
    }
    const authenticate = (_role: string, username: string) => nodePoolAdapter(new Pool({ host: environment.host, port: environment.port, database: environment.database,
      user: username, password: "synthetic-scheduling-role-proof", max: 1, connectionTimeoutMillis: 5000, ssl: false }));
    deepEqual(await proveSchedulingDatabaseAccess(policy, authenticate), manifestIdentity);
    deepEqual(await grantSchedulingDatabaseAccess(admin, policy), observed, "Grant continuation is repeatable without role reactivation or history replacement.");
    await rawPool.query({ text: `GRANT USAGE ON SCHEMA "${policy.otherSchema}" TO "${policy.workerUsername}"` });
    await rawPool.query({ text: `GRANT SELECT ON "${policy.otherSchema}".platform_schedule TO "${policy.workerUsername}"` });
    await rejects(() => proveSchedulingDatabaseAccess(policy, authenticate), "Cross-scope effective access must fail the real SQL probe.");
    await rawPool.query({ text: `REVOKE SELECT ON "${policy.otherSchema}".platform_schedule FROM "${policy.workerUsername}"` });
    await rawPool.query({ text: `REVOKE USAGE ON SCHEMA "${policy.otherSchema}" FROM "${policy.workerUsername}"` });
    await rawPool.query({ text: `GRANT "${policy.migrationUsername}" TO "${policy.workerUsername}"` });
    await rejects(() => proveSchedulingDatabaseAccess(policy, authenticate), "Even NOINHERIT membership in another role must be rejected.");
    await rawPool.query({ text: `REVOKE "${policy.migrationUsername}" FROM "${policy.workerUsername}"` });
    await rawPool.query({ text: `GRANT INSERT ON "${policy.manifest.schema}".platform_processing TO "${policy.dispatchUsername}"` });
    await rejects(() => proveSchedulingDatabaseAccess(policy, authenticate), "A hidden INSERT grant must fail even when SELECT on that table is denied.");
    await rawPool.query({ text: `REVOKE INSERT ON "${policy.manifest.schema}".platform_processing FROM "${policy.dispatchUsername}"` });
    deepEqual(await proveSchedulingDatabaseAccess(policy, authenticate), manifestIdentity);
  }
  deepEqual(await snapshot(), original, "Every pre-existing application, schedule, outbox, processing and migration row must remain byte-for-byte unchanged by grants and rolled-back role probes.");
}

async function baselineSchedulingEngineSafety(rawPool: Pool, configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_namespace WHERE nspname = 'platform'"), 0);
  await rawPool.query({ text: 'CREATE SCHEMA "platform"' });
  const pool = nodePoolAdapter(rawPool), selectedConfiguration = { ...configuration, schema: "platform" };
  required(await createPostgreSqlMigrationRunner(selectedConfiguration, { pool }, "stage3-local").apply(kanbienCoreServerSchedulingMigrationManifest("platform")));
  const clock = fixedClock(fixtureStart);
  const schedules = createPostgreSqlPlatformScheduleStore({ configuration: selectedConfiguration, pool });
  const outbox = createPostgreSqlPlatformOutboxStore({ configuration: selectedConfiguration, pool });
  const processing = createPostgreSqlPlatformProcessingStore({ configuration: selectedConfiguration, pool });
  const persistence = createKanbienCoreServerPostgreSqlPersistenceRuntime({ pool, schema: "platform" });
  const app = createKanbienCoreServerSchedulingApp({ persistence, schedules, outbox, clock });
  const owner = required(platformPersistenceLeaseOwner("baseline-scheduled-proof"));
  const makeWorker = () => createPlatformWorkerShell({ apps: [app], deps: createPlatformTestMountDeps({ clock }),
    diagnosticCatalogs: [platformPersistenceDiagnosticCatalog],
    durableOutboxProcessing: { outbox, processingStore: processing, owner, leaseDurationMs: 10_000 } });
  const worker = required(await makeWorker());
  required(await worker.start());
  try {
    integrationPhase = "baseline-native-workload-measurement";
    const measuredQueue = inMemoryQueue();
    const measuredRelay = createPlatformOutboxRelay({ outbox, queue: measuredQueue, clock, owner, leaseDurationMs: 10_000 });
    const measuredDelivery = createPlatformScheduleDelivery({ clock, scheduleStore: schedules,
      createOutboxEntry: createPlatformScheduleJobOutboxFactory({ jobs: worker.mounted.jobs, clock,
        deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")) }) });
    await measureSchedulingWorkload(rawPool, "core-server-persistence", async index => {
      const id = required(uuid(`${(0x36000000 + index).toString(16)}-1234-4567-8abc-123456789abc`));
      required(await schedules.create(required(createPlatformSchedule({ jobName: kanbienCoreScheduledProofJobName, dueAt: at(0) }, { generate: () => ok(id) }))));
      equal(required(await measuredDelivery.runOnce()).deliveryCreated, 1);
      equal(required(await measuredRelay.runOnce()).status, "published");
      const message = measuredQueue.messages.shift(); assertOk(message !== undefined);
      equal(required(await worker.runDelivery(message)).status, "succeeded");
      equal((await processing.get(outboxEntryId(String(id))))?.state, "completed");
      equal((await persistence.readAcceptanceRecord(String(id))).outcome, "found");
    });
    const schedule = required(await schedules.create(required(createPlatformSchedule({ jobName: kanbienCoreScheduledProofJobName, dueAt: at(0) },
      { generate: () => uuid("34000001-1234-4567-8abc-123456789abc") }))));
    const delivery = createPlatformScheduleDelivery({ clock, scheduleStore: schedules,
      createOutboxEntry: createPlatformScheduleJobOutboxFactory({ jobs: worker.mounted.jobs, clock,
        deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")) }) });
    equal(required(await delivery.runOnce()).deliveryCreated, 1);
    equal(required(await delivery.runOnce()).deliveryCreated, 0);
    const queue = inMemoryQueue();
    const relay = createPlatformOutboxRelay({ outbox, queue, clock, owner, leaseDurationMs: 10_000 });
    equal(required(await relay.runOnce()).status, "published");
    equal(queue.messages.length, 1);
    const message = queue.messages[0]!;
    const delivered = required(await worker.runDelivery(message));
    equal(delivered.status, "succeeded");
    equal((await outbox.get(outboxEntryId(String(schedule.id))))?.state, "published");
    const completed = await processing.get(outboxEntryId(String(schedule.id)));
    equal(completed?.state, "completed");
    equal(completed?.completion?.outcome, "succeeded");
    const accepted = await persistence.readAcceptanceRecord(String(schedule.id));
    equal(accepted.outcome, "found");
    if (accepted.outcome === "found") assertOk(/^[a-f0-9]{64}$/.test(accepted.record.factDigest));
    // The harmless business action is itself repeat-safe, independently of
    // worker deduplication. It must not generate another acceptance record.
    await worker.mounted.jobs[0]!.handler.handle(message, {} as never);
    const reconstructed = required(await makeWorker());
    required(await reconstructed.start());
    try { equal(required(await reconstructed.runDelivery(message)).status, "succeeded"); }
    finally { required(await reconstructed.shutdown()); }
    deepEqual(await processing.get(outboxEntryId(String(schedule.id))), completed, "A restarted worker must retain completed durable state without another claim.");
    equal(await count(rawPool, 'SELECT COUNT(*)::integer AS count FROM "platform"."core_server_persistence_acceptance" WHERE record_id = $1', [schedule.id]), 1);
    equal(await count(rawPool, 'SELECT COUNT(*)::integer AS count FROM "platform"."platform_outbox" WHERE id = $1', [schedule.id]), 1);
  } finally { required(await worker.shutdown()); }
}

async function scheduleEngineSafety(rawPool: Pool, configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const pool = nodePoolAdapter(rawPool);
  const store = createPostgreSqlPlatformScheduleStore({ configuration, pool });
  const fixtureIds = ["31000001-1234-4567-8abc-123456789abc", "31000002-1234-4567-8abc-123456789abc",
    "31000003-1234-4567-8abc-123456789abc", "31000004-1234-4567-8abc-123456789abc",
    "31000005-1234-4567-8abc-123456789abc", "31000006-1234-4567-8abc-123456789abc"] as const;
  const make = (id: string, seconds: number) => required(createPlatformSchedule({
    jobName: required(platformJobName("platform-smoke.scheduling.probe")), dueAt: at(seconds),
  }, { generate: () => uuid(id) }));
  const envelope = (schedule: PlatformSchedule, suffix: string) => outboxEntry({
    id: outboxEntryId(`scheduler-engine-${suffix}`),
    subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(schedule.id)) }),
    messageType: required(outboxMessageType("platform.schedule.due")),
    deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")), createdAt: at(10),
  });
  const concurrent = required(await store.create(make(fixtureIds[0], 0)));
  const left = envelope(concurrent, "concurrent-left"), right = envelope(concurrent, "concurrent-right");
  const race = required(await store.create(make(fixtureIds[1], 0)));
  const raceEnvelope = envelope(race, "block-race");
  try {
    const handovers = await Promise.all([
      store.handoverDue({ scheduleId: concurrent.id, asOf: at(10), outboxEntry: left }),
      createPostgreSqlPlatformScheduleStore({ configuration, pool }).handoverDue({ scheduleId: concurrent.id, asOf: at(10), outboxEntry: right }),
    ]);
    deepEqual(handovers.map(result => required(result).disposition).sort(), ["outbox-already-created", "outbox-created"]);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE id = ANY($1::text[])`, [[left.id, right.id]]), 1);
    const delivered = await store.get(concurrent.id);
    equal(delivered?.state, "delivery-created");
    assertOk(delivered?.outboxEntryId === left.id || delivered?.outboxEntryId === right.id);

    const blockedOrDelivered = await Promise.all([
      store.blockDue({ scheduleId: race.id, asOf: at(10) }),
      store.handoverDue({ scheduleId: race.id, asOf: at(10), outboxEntry: raceEnvelope }),
    ]);
    blockedOrDelivered.forEach(result => equal(result.ok, true));
    const raceState = await store.get(race.id);
    assertOk(raceState?.state === "blocked-job-unavailable" || raceState?.state === "delivery-created");
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE id = $1`, [raceEnvelope.id]), raceState.state === "delivery-created" ? 1 : 0);

    integrationPhase = "schedule-public-concurrent-passes";
    const passSchedule = required(await store.create(make(fixtureIds[4], 0)));
    const makeDelivery = (suffix: string) => createPlatformScheduleDelivery({
      clock: fixedClock(new Date(at(10))), maximumSchedules: 10,
      scheduleStore: createPostgreSqlPlatformScheduleStore({ configuration, pool }),
      createOutboxEntry: selected => envelope(selected, suffix),
    });
    const passes = await Promise.all([makeDelivery("public-pass").runOnce(), makeDelivery("public-pass").runOnce()]);
    equal(passes.reduce((total, result) => total + required(result).deliveryCreated, 0), 1);
    const passState = await store.get(passSchedule.id);
    equal(passState?.state, "delivery-created"); equal(passState?.outboxEntryId, outboxEntryId("scheduler-engine-public-pass"));
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE id = $1`, [passState.outboxEntryId]), 1);
    equal(required(await makeDelivery("public-pass").runOnce()).deliveryCreated, 0);

    integrationPhase = "schedule-handover-after-insert-rollback";
    const rollback = required(await store.create(make(fixtureIds[5], 0)));
    const rollbackEnvelope = envelope(rollback, "rollback");
    try {
      // This BEFORE UPDATE trigger can only report the selected 40001 fault
      // after seeing the outbox INSERT inside the same real transaction.
      await rawPool.query({ text: `CREATE FUNCTION "${schema}".reject_schedule_after_insert() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM "${schema}".platform_outbox WHERE id = NEW.outbox_entry_id) THEN
          RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'Expected owned outbox insert is absent';
        END IF;
        RAISE EXCEPTION USING ERRCODE = '40001', MESSAGE = 'Controlled disposable transition failure'; END $$` });
      await rawPool.query({ text: `CREATE TRIGGER reject_schedule_after_insert BEFORE UPDATE ON "${schema}".platform_schedule
        FOR EACH ROW WHEN (NEW.state = 'delivery-created') EXECUTE FUNCTION "${schema}".reject_schedule_after_insert()` });
      const rejected = await makeDelivery("rollback").runOnce();
      equal(rejected.ok, false);
      if (!rejected.ok) equal(rejected.error.params?.["provider_failure_class"], "transaction_rolled_back");
      deepEqual(await store.get(rollback.id), rollback, "A rejected transition must leave the reminder waiting.");
      equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE id = $1`, [rollbackEnvelope.id]), 0,
        "The INSERT observed by the failing trigger must roll back with the reminder transition.");
    } finally {
      await rawPool.query({ text: `DROP TRIGGER IF EXISTS reject_schedule_after_insert ON "${schema}".platform_schedule` });
      await rawPool.query({ text: `DROP FUNCTION IF EXISTS "${schema}".reject_schedule_after_insert()` });
    }
    equal(required(await makeDelivery("rollback").runOnce()).deliveryCreated, 1);
    equal((await store.get(rollback.id))?.outboxEntryId, rollbackEnvelope.id);
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_outbox" WHERE id = $1`, [rollbackEnvelope.id]), 1);

    integrationPhase = "schedule-engine-corrupt-row-repair";
    const corrupt = required(await store.create(make(fixtureIds[2], -2)));
    const healthy = required(await store.create(make(fixtureIds[3], -1)));
    await rawPool.query({ text: `UPDATE "${schema}"."platform_schedule" SET job_name = 'invalid job name' WHERE id = $1`, values: [corrupt.id] });
    equal((await store.listDue({ asOf: at(10), limit: 1 })).ok, false, "Read-only inspection must not silently hide corrupt rows.");
    deepEqual(required(await store.listDue({ asOf: at(10), limit: 1, blockInvalid: true })), []);
    equal((await rawPool.query({ text: `SELECT state FROM "${schema}"."platform_schedule" WHERE id = $1`, values: [corrupt.id] })).rows[0]?.state, "blocked-invalid-row");
    equal((await store.resumeBlocked(corrupt.id)).ok, false, "Resuming must validate before changing the blocked state.");
    equal((await rawPool.query({ text: `SELECT state FROM "${schema}"."platform_schedule" WHERE id = $1`, values: [corrupt.id] })).rows[0]?.state, "blocked-invalid-row");
    deepEqual(required(await store.listDue({ asOf: at(10), limit: 1, blockInvalid: true })).map(item => item.id), [healthy.id], "The next bounded pass can progress beyond the corrupt oldest row.");
    await rawPool.query({ text: `UPDATE "${schema}"."platform_schedule" SET job_name = $2 WHERE id = $1`, values: [corrupt.id, corrupt.jobName] });
    equal(required(await store.resumeBlocked(corrupt.id)).state, "waiting");
    deepEqual(required(await store.listDue({ asOf: at(10), limit: 1 })).map(item => item.id), [corrupt.id]);
  } finally {
    await rawPool.query({ text: `DELETE FROM "${schema}"."platform_schedule" WHERE id = ANY($1::uuid[])`, values: [[...fixtureIds]] });
    await rawPool.query({ text: `DELETE FROM "${schema}"."platform_outbox" WHERE id = ANY($1::text[])`, values: [[left.id, right.id, raceEnvelope.id, "scheduler-engine-public-pass", "scheduler-engine-rollback"]] });
  }
}

async function scheduleSchemaIsolation(rawPool: Pool, configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const scopes = ["scheduler_isolation_left", "scheduler_isolation_right"] as const;
  for (const scope of scopes) equal(await count(rawPool,
    "SELECT COUNT(*)::integer AS count FROM pg_namespace WHERE nspname = $1", [scope]), 0);
  const created: string[] = [], pool = nodePoolAdapter(rawPool);
  try {
    for (const scope of scopes) {
      await rawPool.query({ text: `CREATE SCHEMA "${scope}"` }); created.push(scope);
      required(await createPostgreSqlMigrationRunner({ ...configuration, schema: scope }, { pool }, "stage3-local")
        .apply(kanbienCoreServerSchedulingMigrationManifest(scope)));
    }
    const stores = scopes.map(scope => {
      const options = { configuration: { ...configuration, schema: scope }, pool };
      return { schedules: createPostgreSqlPlatformScheduleStore(options), outbox: createPostgreSqlPlatformOutboxStore(options),
        processing: createPostgreSqlPlatformProcessingStore(options) };
    });
    const left = stores[0]!, right = stores[1]!;
    const make = (seconds: number) => required(createPlatformSchedule({
      jobName: required(platformJobName("platform-smoke.scheduling.probe")), dueAt: at(seconds),
    }, { generate: () => uuid("34000001-1234-4567-8abc-123456789abc") }));
    const leftSchedule = required(await left.schedules.create(make(0)));
    equal(await right.schedules.get(leftSchedule.id), null);
    const rightSchedule = required(await right.schedules.create(make(20)));
    required(await right.schedules.blockDue({ scheduleId: rightSchedule.id, asOf: at(20) }));
    deepEqual(await left.schedules.get(leftSchedule.id), leftSchedule);
    deepEqual(required(await right.schedules.resumeBlocked(rightSchedule.id)), rightSchedule);
    const entry = (selected: PlatformSchedule) => outboxEntry({ id: outboxEntryId(String(selected.id)),
      subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(selected.id)) }),
      messageType: required(outboxMessageType("platform.schedule.due")), createdAt: selected.dueAt,
      deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")) });
    const leftEntry = entry(leftSchedule), rightEntry = entry(rightSchedule);
    required(await left.schedules.handoverDue({ scheduleId: leftSchedule.id, asOf: at(10), outboxEntry: leftEntry }));
    equal(await right.outbox.get(rightEntry.id), null);
    deepEqual(await right.schedules.get(rightSchedule.id), rightSchedule);
    equal(required(await right.schedules.listDue({ asOf: at(10), limit: 10 })).length, 0);
    equal(required(await right.schedules.handoverDue({ scheduleId: rightSchedule.id, asOf: at(10), outboxEntry: rightEntry })).disposition, "not-due");
    required(await right.schedules.handoverDue({ scheduleId: rightSchedule.id, asOf: at(20), outboxEntry: rightEntry }));
    deepEqual((await left.outbox.get(leftEntry.id))?.entry, leftEntry);
    deepEqual((await right.outbox.get(rightEntry.id))?.entry, rightEntry);
    const leftOwner = required(platformPersistenceLeaseOwner("scope-left")), rightOwner = required(platformPersistenceLeaseOwner("scope-right"));
    const claim = await left.outbox.claim({ id: leftEntry.id, owner: leftOwner, acquiredAt: at(20), leaseDurationMs: 10_000 });
    equal((await right.outbox.get(rightEntry.id))?.state, "pending");
    required(await left.outbox.markPublished({ id: leftEntry.id, fence: claimedFence(claim), publishedAt: at(21) }));
    equal((await right.outbox.get(rightEntry.id))?.state, "pending");
    const leftClaim = await left.processing.claim({ outboxEntryId: leftEntry.id, owner: leftOwner, acquiredAt: at(21), leaseDurationMs: 10_000 });
    equal(await right.processing.get(rightEntry.id), null);
    const rightClaim = required(await right.processing.claim({ outboxEntryId: rightEntry.id, owner: rightOwner, acquiredAt: at(22), leaseDurationMs: 10_000 }));
    required(await left.processing.complete({ outboxEntryId: leftEntry.id, fence: claimedFence(leftClaim), outcome: "succeeded", completedAt: at(23) }));
    deepEqual(await right.processing.get(rightEntry.id), rightClaim.record);
    equal((await left.processing.get(leftEntry.id))?.state, "completed");
  } finally {
    // Only the two fixed namespaces proved absent and created above are owned.
    for (const scope of created.reverse()) await rawPool.query({ text: `DROP SCHEMA "${scope}" CASCADE` });
  }
}

async function entityReminderEngineSafety(rawPool: Pool, configuration: PostgreSqlPersistenceConfiguration): Promise<void> {
  const selectedConfiguration = { ...configuration, schema: "entity_smoke" };
  // This manifest has a fixed target schema. Refuse any previously populated
  // namespace: this fixture must never become a cleanup procedure for live data.
  equal(await count(rawPool, "SELECT COUNT(*)::integer AS count FROM pg_namespace WHERE nspname = 'entity_smoke'"), 0);
  await rawPool.query({ text: 'CREATE SCHEMA "entity_smoke"' });
  const pool = nodePoolAdapter(rawPool);
  required(await createPostgreSqlMigrationRunner(selectedConfiguration, { pool }, "stage3-local").apply(entitySmokeMigrationManifest()));
  const runtime = createEntitySmokePostgreSqlRuntime(pool, selectedConfiguration);
  assertOk(runtime.deletionTransaction !== undefined);
  const schedules = createPostgreSqlPlatformScheduleStore({ configuration: selectedConfiguration, pool });
  let ordinal = 0;
  const services: TestEntityServiceDependencies = { repository: runtime.repository, clock: fixedClock(fixtureStart),
    uuidGenerator: { generate: () => uuid(`${(0x32000000 + ++ordinal).toString(16)}-1234-4567-8abc-123456789abc`) },
    lifecyclePolicy: required(recordLifecyclePolicy({ recoveryWindowMs: 60_000, legalHoldCheckRequired: true,
      retentionPolicy: required(recordRetentionPolicyReference("entity-smoke.retention")) })),
    expiredPurgeReminder: { jobName: entitySmokeExpiredPurgeJobName, store: schedules }, deletionTransaction: runtime.deletionTransaction };
  const input = { integerValue: 7, uuidValue: "33000000-1234-4567-8abc-123456789abc", occurredAt: at(-1),
    label: "Owned PostgreSQL scheduling fixture", status: "draft" as const, enabled: true, categories: ["alpha"] as const,
    notes: ["owned fixture"], description: null, reviewedAt: null, secondaryCategories: null };
  const archived = async () => {
    const entity = required(await createTestEntityService(input, services));
    return required(await archiveTestEntityService(entity.id, services));
  };
  const scheduleFor = async (entity: TestEntity) => {
    const due = required(await schedules.listDue({ asOf: at(1_000), limit: 100 }));
    const schedule = due.find(item => item.subject?.id === String(entity.id));
    assertOk(schedule !== undefined);
    return schedule;
  };
  integrationPhase = "entity-native-workload-measurement";
  const measuredClock = fixedClock(new Date(at(300.001)));
  const measuredOutbox = createPostgreSqlPlatformOutboxStore({ configuration: selectedConfiguration, pool });
  const measuredProcessing = createPostgreSqlPlatformProcessingStore({ configuration: selectedConfiguration, pool });
  const measuredOwner = required(platformPersistenceLeaseOwner("entity-native-measurement"));
  const measuredWorker = required(await createPlatformWorkerShell({
    apps: [createEntitySmokeSchedulingApp({ pool, clock: measuredClock, schedules, outbox: measuredOutbox, close: async () => undefined })],
    deps: createPlatformTestMountDeps({ clock: measuredClock }), diagnosticCatalogs: [platformPersistenceDiagnosticCatalog],
    durableOutboxProcessing: { outbox: measuredOutbox, processingStore: measuredProcessing, owner: measuredOwner, leaseDurationMs: 10_000 },
  }));
  required(await measuredWorker.start());
  try {
    const measuredQueue = inMemoryQueue();
    const measuredDelivery = createPlatformScheduleDelivery({ clock: measuredClock, scheduleStore: schedules,
      createOutboxEntry: createPlatformScheduleJobOutboxFactory({ jobs: measuredWorker.mounted.jobs, clock: measuredClock,
        deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")) }) });
    const measuredRelay = createPlatformOutboxRelay({ outbox: measuredOutbox, queue: measuredQueue, clock: measuredClock,
      owner: measuredOwner, leaseDurationMs: 10_000 });
    await measureSchedulingWorkload(rawPool, "entity-smoke", async () => {
      const entity = required(await deleteTestEntityService((await archived()).id, services));
      const reminder = await scheduleFor(entity);
      equal(required(await measuredDelivery.runOnce()).deliveryCreated, 1);
      equal(required(await measuredRelay.runOnce()).status, "published");
      const message = measuredQueue.messages.shift(); assertOk(message !== undefined);
      equal(required(await measuredWorker.runDelivery(message)).status, "succeeded");
      equal((await measuredProcessing.get(outboxEntryId(String(reminder.id))))?.state, "completed");
      equal(await runtime.repository.get(entity.id), null);
    });
  } finally { required(await measuredWorker.shutdown()); }
  await proveNativeDelivery();
  integrationPhase = "entity-atomic-reminder-and-guarded-purge";
  const selected = await archived();
  const deleted = required(await deleteTestEntityService(selected.id, services));
  const reminder = await scheduleFor(deleted);
  deepEqual(reminder.subject, { kind: "entity-smoke.test-entity", id: deleted.id });
  equal(reminder.dueAt, at(300.001));
  equal((await runtime.repository.get(deleted.id))?.lifecycle.state, "deleted");

  const rollback = await archived();
  const failedEntityWrite = await deleteTestEntityService(rollback.id, { ...services, deletionTransaction: {
    run: operation => runtime.deletionTransaction!.run(scope => operation({ ...scope,
      repository: { ...scope.repository, save: (next, expected) => scope.repository.save({ ...next, integerValue: 0.5 }, expected) } })),
  } });
  equal(failedEntityWrite.ok, false, "A real PostgreSQL integer rejection after reminder INSERT must roll back both participants.");
  deepEqual(await runtime.repository.get(rollback.id), rollback);
  equal(await count(rawPool, 'SELECT COUNT(*)::integer AS count FROM "entity_smoke"."platform_schedule" WHERE subject_id = $1', [rollback.id]), 0);
  const failedReminderWrite = await deleteTestEntityService(rollback.id, { ...services,
    uuidGenerator: { generate: () => uuid(String(reminder.id)) } });
  equal(failedReminderWrite.ok, false, "A real duplicate reminder INSERT must not logically delete the entity.");
  deepEqual(await runtime.repository.get(rollback.id), rollback);
  deepEqual(await schedules.get(reminder.id), reminder);

  const snapshot = required(await createTestEntityService(input, services));
  const differentId = required(uuid("33000001-1234-4567-8abc-123456789abc"));
  const expectedDifferences: readonly Partial<TestEntity>[] = [
    { id: deleted.id }, { integerValue: 8 }, { uuidValue: differentId }, { occurredAt: at(-2) }, { label: "different" },
    { status: "active" }, { enabled: false }, { categories: ["beta"] }, { notes: ["different"] },
    { description: "different" }, { reviewedAt: at(-2) }, { secondaryCategories: ["gamma"] },
    { visibility: "archived" }, { lifecycle: deleted.lifecycle }, { createdAt: at(-2) }, { updatedAt: at(-2) },
  ];
  for (const difference of expectedDifferences) {
    const rejected = await runtime.repository.save({ ...snapshot, label: "stale must not overwrite" }, { ...snapshot, ...difference });
    equal(rejected.ok, false, `The expected ${Object.keys(difference)[0]} field participates in the atomic predicate.`);
    if (!rejected.ok) equal(rejected.error.code, "TEST_ENTITY_WRITE_CONFLICT");
    deepEqual(await runtime.repository.get(snapshot.id), snapshot);
  }
  const changed = required(await updateTestEntityService(snapshot.id, { notes: ["same millisecond edit"],
    description: "non-null", reviewedAt: at(-2), secondaryCategories: [] }, services));
  equal(changed.updatedAt, snapshot.updatedAt, "The proof does not depend on clock advancement.");
  const stale = await runtime.repository.save({ ...snapshot, label: "stale snapshot" }, snapshot);
  equal(stale.ok, false);
  deepEqual(await runtime.repository.get(snapshot.id), changed);
  const nullableAgain = required(await updateTestEntityService(snapshot.id, { description: null, reviewedAt: null, secondaryCategories: null }, services));
  deepEqual(await runtime.repository.get(snapshot.id), nullableAgain, "JSONB arrays, nulls and timestamps match real PostgreSQL parameter types.");

  const extendedRecovery = required(await deleteTestEntityService((await archived()).id, { ...services,
    lifecyclePolicy: required(recordLifecyclePolicy({ recoveryWindowMs: 600_000, legalHoldCheckRequired: true,
      retentionPolicy: required(recordRetentionPolicyReference("entity-smoke.retention")) })) }));
  if (extendedRecovery.lifecycle.state !== "deleted") throw new Error("Expected an owned extended-recovery fixture.");
  const recoveryCondition = { id: extendedRecovery.id, deletedAt: extendedRecovery.lifecycle.deletedAt,
    asOf: at(300.001), retentionWindowMs: testEntityRetentionWindowMs };
  equal(required(await runtime.repository.purgeArchivedDeleted(recoveryCondition)), false, "Elapsed retention does not override recovery.");
  equal(required(await runtime.repository.purgeArchivedDeleted({ ...recoveryCondition, asOf: at(600) })), false);
  equal((await scheduleFor(extendedRecovery)).dueAt, at(600.001));
  equal(required(await runtime.repository.purgeArchivedDeleted({ ...recoveryCondition, asOf: at(600.001) })), true);

  const unrelated = required(await deleteTestEntityService((await archived()).id, services));
  const unrelatedBefore = await runtime.repository.get(unrelated.id);
  if (deleted.lifecycle.state !== "deleted") throw new Error("Expected an owned deleted fixture.");
  const condition = { id: deleted.id, deletedAt: deleted.lifecycle.deletedAt, asOf: at(300), retentionWindowMs: testEntityRetentionWindowMs };
  equal(required(await runtime.repository.purgeArchivedDeleted(condition)), false, "Exact retention expiry must not purge.");
  // A real row mutation lands between the service's read and final conditional
  // DELETE; the stale selected generation can no longer remove the new state.
  let intervened = false;
  const concurrentRestore = { ...services, clock: fixedClock(new Date(at(300.001))), repository: { ...runtime.repository,
    purgeArchivedDeleted: async (selectedCondition: typeof condition) => {
      intervened = true;
      required(await restoreLogicallyDeletedTestEntityService(deleted.id, { ...services, clock: fixedClock(new Date(at(30))) }));
      return runtime.repository.purgeArchivedDeleted(selectedCondition);
    } } };
  deepEqual(required(await purgeExpiredTestEntityService(reminder, concurrentRestore)), { inspected: 1, purged: 0 });
  equal(intervened, true);
  equal((await runtime.repository.get(deleted.id))?.lifecycle.state, "active");
  const laterDeleted = required(await deleteTestEntityService(deleted.id, { ...services, clock: fixedClock(new Date(at(31))) }));
  equal(required(await runtime.repository.purgeArchivedDeleted({ ...condition, asOf: at(1_000) })), false, "An old generation cannot remove a later deletion.");
  deepEqual(required(await purgeExpiredTestEntityService(reminder, { ...services, clock: fixedClock(new Date(at(1_000))) })), { inspected: 1, purged: 0 });
  const laterReminder = required(await schedules.listDue({ asOf: at(1_000), limit: 100 })).find(item => item.subject?.id === String(deleted.id) && item.id !== reminder.id);
  assertOk(laterReminder !== undefined);
  deepEqual(required(await purgeExpiredTestEntityService(laterReminder, { ...services, clock: fixedClock(new Date(at(1_000))) })), { inspected: 1, purged: 1 });
  equal(await runtime.repository.get(laterDeleted.id), null);
  deepEqual(await runtime.repository.get(unrelated.id), unrelatedBefore, "Another eligible deleted row remains byte-equivalent.");
  deepEqual(required(await purgeExpiredTestEntityService(laterReminder, { ...services, clock: fixedClock(new Date(at(1_000))) })), { inspected: 0, purged: 0 });

  async function proveNativeDelivery(): Promise<void> {
    integrationPhase = "entity-native-delivery-before-due";
    const selected = required(await deleteTestEntityService((await archived()).id, services));
    const retryEntity = required(await deleteTestEntityService((await archived()).id, services));
    const uncertainEntity = required(await deleteTestEntityService((await archived()).id, services));
    const unrelated = required(await deleteTestEntityService((await archived()).id, services));
    const restoredDeleted = required(await deleteTestEntityService((await archived()).id, services));
    const restored = required(await restoreLogicallyDeletedTestEntityService(restoredDeleted.id, {
      ...services, clock: fixedClock(new Date(at(30))) }));
    const active = required(await createTestEntityService(input, services));
    const future = required(await deleteTestEntityService((await archived()).id, {
      ...services, clock: fixedClock(new Date(at(60))) }));
    const selectedReminder = await scheduleFor(selected), retryReminder = await scheduleFor(retryEntity);
    const uncertainReminder = await scheduleFor(uncertainEntity);
    const unrelatedReminder = await scheduleFor(unrelated), restoredReminder = await scheduleFor(restored);
    const futureReminder = await scheduleFor(future);
    const controls = [unrelated, restored, active, future];
    let current = Date.parse(at(299.999)), workerOrdinal = 0;
    const clock = { now: () => new Date(current) };
    const outbox = createPostgreSqlPlatformOutboxStore({ configuration: selectedConfiguration, pool });
    const processing = createPostgreSqlPlatformProcessingStore({ configuration: selectedConfiguration, pool });
    const makeWorker = () => createPlatformWorkerShell({
      apps: [createEntitySmokeSchedulingApp({ pool, clock, schedules, outbox, close: async () => undefined })],
      deps: createPlatformTestMountDeps({ clock }), diagnosticCatalogs: [platformPersistenceDiagnosticCatalog],
      maxAttempts: 3, retryBackoffMs: () => 5_000,
      durableOutboxProcessing: {
        outbox: createPostgreSqlPlatformOutboxStore({ configuration: selectedConfiguration, pool }),
        processingStore: createPostgreSqlPlatformProcessingStore({ configuration: selectedConfiguration, pool }),
        owner: required(platformPersistenceLeaseOwner(`entity-native-worker-${++workerOrdinal}`)), leaseDurationMs: 10_000,
      },
    });
    const registration = required(await makeWorker());
    required(await registration.start());
    try {
      const delivery = createPlatformScheduleDelivery({ clock, scheduleStore: schedules, maximumSchedules: 10,
        createOutboxEntry: createPlatformScheduleJobOutboxFactory({ jobs: registration.mounted.jobs, clock,
          deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")) }) });
      equal(required(await delivery.runOnce()).deliveryCreated, 0);
      current = Date.parse(at(300));
      equal(required(await delivery.runOnce()).deliveryCreated, 0, "Exact retention expiry cannot hand over a cleanup reminder.");
      deepEqual(await runtime.repository.get(selected.id), selected);
      equal(await outbox.get(outboxEntryId(String(selectedReminder.id))), null);
      current = Date.parse(at(300.001));
      equal(required(await delivery.runOnce()).deliveryCreated, 5);
      equal(required(await delivery.runOnce()).deliveryCreated, 0);
    } finally { required(await registration.shutdown()); }

    integrationPhase = "entity-native-delivery-relay";
    const bodies: string[] = [], visibility: { receipt: string; seconds: number }[] = [];
    const queueUrl = "https://sqs.eu-west-1.amazonaws.com/123456789012/entity-native-proof";
    const queueArn = "arn:aws:sqs:eu-west-1:123456789012:entity-native-proof";
    const client = { async send(command: unknown) {
      const request = command as { constructor: { name: string }; input: {
        QueueUrl?: string; MessageBody?: string; ReceiptHandle?: string; VisibilityTimeout?: number } };
      equal(request.input.QueueUrl, queueUrl);
      if (request.constructor.name === "SendMessageCommand") {
        assertOk(typeof request.input.MessageBody === "string"); bodies.push(request.input.MessageBody); return {};
      }
      if (request.constructor.name === "ChangeMessageVisibilityCommand") {
        assertOk(typeof request.input.ReceiptHandle === "string" && typeof request.input.VisibilityTimeout === "number");
        visibility.push({ receipt: request.input.ReceiptHandle, seconds: request.input.VisibilityTimeout }); return {};
      }
      throw new Error("Native delivery must not start another receive or acknowledgement loop.");
    } };
    const relay = createPlatformOutboxRelay({
      outbox: createPostgreSqlPlatformOutboxStore({ configuration: selectedConfiguration, pool }),
      queue: createPlatformSqsQueue<PlatformOutboxQueuePayload>({ queueUrl, client }), clock,
      owner: required(platformPersistenceLeaseOwner("entity-native-relay")), leaseDurationMs: 10_000,
    });
    for (let index = 0; index < 5; index++) equal(required(await relay.runOnce()).status, "published");
    equal(required(await relay.runOnce()).status, "idle");
    equal(bodies.length, 5);
    const bodyFor = (reminder: PlatformSchedule) => {
      const body = bodies.find(value => JSON.parse(value).id === String(reminder.id));
      assertOk(body !== undefined);
      deepEqual(JSON.parse(body).payload, { outboxEntryId: String(reminder.id) }, "Transport carries only the durable outbox reference.");
      return body;
    };
    let deliveryFailureCode: string | undefined;
    const deliver = async (reminder: PlatformSchedule, nativeId: string) => {
      deliveryFailureCode = undefined;
      const worker = required(await makeWorker());
      required(await worker.start());
      try {
        const batch = createPlatformSqsLambdaBatchHandler({ expectedSourceArn: queueArn, maximumBatchSize: 1,
          visibility: createPlatformSqsWorkerQueue({ queueUrl, client, waitTimeSeconds: 0, visibilityTimeoutSeconds: 360 }),
          async processMessage(message) {
            const result = await worker.runDelivery(message);
            if (!result.ok) { deliveryFailureCode = result.error.code; return { disposition: "retry" }; }
            if (result.value.status === "succeeded") return { disposition: "acknowledge" };
            return result.value.status === "retry" ? { disposition: "retry", delayMs: result.value.delayMs } : { disposition: "retry" };
          } });
        return await batch.run({ Records: [{ eventSource: "aws:sqs", eventSourceARN: queueArn,
          messageId: nativeId, receiptHandle: `${nativeId}-receipt`, body: bodyFor(reminder) }] });
      } finally { required(await worker.shutdown()); }
    };
    const processingId = (reminder: PlatformSchedule) => outboxEntryId(String(reminder.id));
    const unchangedControls = async () => {
      for (const entity of controls) deepEqual(await runtime.repository.get(entity.id), entity);
      equal((await schedules.get(futureReminder.id))?.state, "waiting");
      equal(await outbox.get(processingId(futureReminder)), null);
      equal(await processing.get(processingId(unrelatedReminder)), null, "Another eligible row is not processed by the selected job.");
    };

    integrationPhase = "entity-native-delivery-targeted-success";
    deepEqual(await deliver(selectedReminder, "native-owned-success"), { batchItemFailures: [] });
    equal(await runtime.repository.get(selected.id), null);
    const completed = await processing.get(processingId(selectedReminder));
    equal(completed?.state, "completed"); equal(completed?.completion?.outcome, "succeeded");
    equal((await outbox.get(processingId(selectedReminder)))?.state, "published");
    deepEqual(await deliver(selectedReminder, "native-owned-duplicate"), { batchItemFailures: [] });
    deepEqual(await processing.get(processingId(selectedReminder)), completed, "Reconstruction preserves durable completion without another claim.");
    deepEqual(await deliver(restoredReminder, "native-owned-restored"), { batchItemFailures: [] });
    await unchangedControls();

    integrationPhase = "entity-native-delivery-engine-retry";
    // The namespace was absent at fixture entry. This temporary database fault
    // applies only inside that owned disposable schema and is always removed.
    try {
      await rawPool.query({ text: 'CREATE FUNCTION "entity_smoke".native_delivery_reject_delete() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION USING ERRCODE = \'40001\', MESSAGE = \'Controlled disposable delete failure\'; END $$' });
      await rawPool.query({ text: 'CREATE TRIGGER native_delivery_reject_delete BEFORE DELETE ON "entity_smoke".test_entity FOR EACH ROW EXECUTE FUNCTION "entity_smoke".native_delivery_reject_delete()' });
      deepEqual(await deliver(retryReminder, "native-owned-retry"), { batchItemFailures: [{ itemIdentifier: "native-owned-retry" }] });
      deepEqual(await runtime.repository.get(retryEntity.id), retryEntity);
      const failed = await processing.get(processingId(retryReminder));
      equal(failed?.state, "retry-eligible"); equal(failed?.attempt, 1);
      equal(failed?.retryAt, at(305.001)); equal(failed?.completion, undefined);
      deepEqual(visibility, [{ receipt: "native-owned-retry-receipt", seconds: 5 }]);
      await unchangedControls();
    } finally {
      await rawPool.query({ text: 'DROP TRIGGER IF EXISTS native_delivery_reject_delete ON "entity_smoke".test_entity' });
      await rawPool.query({ text: 'DROP FUNCTION IF EXISTS "entity_smoke".native_delivery_reject_delete()' });
    }
    integrationPhase = "entity-native-delivery-reconstructed-retry";
    const failed = await processing.get(processingId(retryReminder));
    current = Date.parse(at(305));
    deepEqual(await deliver(retryReminder, "native-owned-retry"), { batchItemFailures: [{ itemIdentifier: "native-owned-retry" }] });
    equal(deliveryFailureCode, "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY");
    deepEqual(await processing.get(processingId(retryReminder)), failed, "A restarted worker cannot claim before persisted retryAt.");
    deepEqual(await runtime.repository.get(retryEntity.id), retryEntity);
    integrationPhase = "entity-native-delivery-retry-due";
    current = Date.parse(at(305.001));
    deepEqual(await deliver(retryReminder, "native-owned-retry"), { batchItemFailures: [] });
    equal(await runtime.repository.get(retryEntity.id), null);
    const recovered = await processing.get(processingId(retryReminder));
    equal(recovered?.state, "completed"); equal(recovered?.completion?.outcome, "succeeded"); equal(recovered?.attempt, 2);
    integrationPhase = "entity-native-delivery-retry-duplicate";
    deepEqual(await deliver(retryReminder, "native-owned-retry-duplicate"), { batchItemFailures: [] });
    deepEqual(await processing.get(processingId(retryReminder)), recovered);
    // A not-yet-due claim stays unacknowledged without changing provider
    // visibility again. Only the actual failed attempt establishes its delay.
    deepEqual(visibility, [{ receipt: "native-owned-retry-receipt", seconds: 5 }]);
    await unchangedControls();

    integrationPhase = "entity-native-completion-write-failure";
    try {
      await rawPool.query({ text: 'CREATE FUNCTION "entity_smoke".native_delivery_reject_completion() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION USING ERRCODE = \'40001\', MESSAGE = \'Controlled disposable completion failure\'; END $$' });
      await rawPool.query({ text: 'CREATE TRIGGER native_delivery_reject_completion BEFORE UPDATE ON "entity_smoke".platform_processing FOR EACH ROW WHEN (NEW.state = \'completed\') EXECUTE FUNCTION "entity_smoke".native_delivery_reject_completion()' });
      deepEqual(await deliver(uncertainReminder, "native-owned-completion"), { batchItemFailures: [{ itemIdentifier: "native-owned-completion" }] });
      equal(deliveryFailureCode, "PLATFORM_WORKER_DURABLE_PROCESSING_FAILED");
      equal(await runtime.repository.get(uncertainEntity.id), null, "The actual deletion committed before completion storage failed.");
      const claim = await processing.get(processingId(uncertainReminder));
      equal(claim?.state, "claimed"); equal(claim?.attempt, 1);
      equal(claim?.lease?.acquiredAt, at(305.001)); equal(claim?.lease?.expiresAt, at(315.001)); equal(claim?.lease?.fence, 1);
      equal(claim?.completion, undefined); equal(claim?.retryAt, undefined);
      await unchangedControls();
    } finally {
      await rawPool.query({ text: 'DROP TRIGGER IF EXISTS native_delivery_reject_completion ON "entity_smoke".platform_processing' });
      await rawPool.query({ text: 'DROP FUNCTION IF EXISTS "entity_smoke".native_delivery_reject_completion()' });
    }
    integrationPhase = "entity-native-completion-lease-protection";
    const uncertainClaim = await processing.get(processingId(uncertainReminder));
    current = Date.parse(at(315));
    deepEqual(await deliver(uncertainReminder, "native-owned-completion"), { batchItemFailures: [{ itemIdentifier: "native-owned-completion" }] });
    equal(deliveryFailureCode, "PLATFORM_WORKER_DURABLE_PROCESSING_BUSY");
    deepEqual(await processing.get(processingId(uncertainReminder)), uncertainClaim);
    integrationPhase = "entity-native-completion-reconstruction";
    current = Date.parse(at(315.001));
    deepEqual(await deliver(uncertainReminder, "native-owned-completion"), { batchItemFailures: [] });
    equal(await runtime.repository.get(uncertainEntity.id), null, "Missing-row replay is a successful no-op.");
    const settled = await processing.get(processingId(uncertainReminder));
    equal(settled?.state, "completed"); equal(settled?.attempt, 2); equal(settled?.completion?.outcome, "succeeded");
    deepEqual(await deliver(uncertainReminder, "native-owned-completion-duplicate"), { batchItemFailures: [] });
    deepEqual(await processing.get(processingId(uncertainReminder)), settled);
    deepEqual(visibility, [{ receipt: "native-owned-retry-receipt", seconds: 5 }], "An uncertain completion is not rewritten as a failed-handler retry.");
    await unchangedControls();
  }
}

async function waitForFixtureAuthentication(environment: ReturnType<typeof localFixtureEnvironment>): Promise<void> {
  // `pg_isready` establishes that the postmaster accepts probes, not that a
  // freshly created container has reached a stable password-authentication
  // boundary. Establish that boundary with the real driver before testing a
  // deliberately rejected password. Bounded retries only cover fixture start;
  // they never turn an expected diagnostic assertion into a pass.
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const pool = new Pool({
      host: environment.host,
      port: environment.port,
      database: environment.database,
      user: "postgres",
      password: environment.password,
      max: 1,
      connectionTimeoutMillis: 1_000,
      ssl: false,
    });
    try {
      const client = await pool.connect();
      client.release();
      return;
    } catch {
      // The fixture is still starting. Provider detail is deliberately not
      // emitted because it can contain connection material.
    } finally {
      await pool.end();
    }
    await new Promise<void>((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("The disposable PostgreSQL fixture did not reach authenticated readiness.");
}

async function bootstrapOwnershipRepeat(environment: ReturnType<typeof localFixtureEnvironment>, rawPool: Pool): Promise<void> {
  const administrator = "rdsbootstrapadmin";
  const migration = "psmoke_bootstrap_migrate";
  const runtime = "psmoke_bootstrap_runtime";
  const bootstrapSchema = "bootstrap_repeat_proof";
  await rawPool.query({ text: `CREATE ROLE ${administrator} LOGIN CREATEROLE PASSWORD 'fixture-admin-password'` });
  await rawPool.query({ text: `GRANT CONNECT, CREATE, TEMPORARY ON DATABASE postgres TO ${administrator}` });
  const adminPool = new Pool({ host: environment.host, port: environment.port, database: environment.database, user: administrator, password: "fixture-admin-password", max: 1, connectionTimeoutMillis: 5_000, ssl: false });
  try {
    for (let pass = 0; pass < 2; pass += 1) {
      await adminPool.query({ text: `DO $$ BEGIN CREATE ROLE ${migration} LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$` });
      await adminPool.query({ text: `DO $$ BEGIN CREATE ROLE ${runtime} LOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$` });
      await adminPool.query({ text: `GRANT CONNECT, CREATE, TEMPORARY ON DATABASE postgres TO ${migration}` });
      await adminPool.query({ text: `GRANT CONNECT ON DATABASE postgres TO ${runtime}` });
      await adminPool.query({ text: `GRANT ${migration} TO CURRENT_USER` });
      await adminPool.query({ text: `CREATE SCHEMA IF NOT EXISTS ${bootstrapSchema} AUTHORIZATION ${migration}` });
      await adminPool.query({ text: `GRANT USAGE ON SCHEMA ${bootstrapSchema} TO ${runtime}` });
    }
  } finally { await adminPool.end(); }
  const ownership = await rawPool.query<{ owner: string }>({ text: `SELECT n.nspowner::regrole::text AS owner FROM pg_namespace n WHERE n.nspname = '${bootstrapSchema}'` });
  equal(ownership.rows[0]?.owner, migration, "Bootstrap must retain migration-schema ownership after a repeat.");
  const runtimePool = new Pool({ host: environment.host, port: environment.port, database: environment.database, user: runtime, password: "fixture-runtime-password", max: 1, connectionTimeoutMillis: 5_000, ssl: false });
  try {
    let rejected = false;
    try { await runtimePool.query({ text: `CREATE TABLE ${bootstrapSchema}.runtime_must_not_create (id text)` }); } catch { rejected = true; }
    equal(rejected, true, "Runtime must not receive schema CREATE through bootstrap.");
  } finally { await runtimePool.end(); }
}

async function bootstrapEffectsReadOnlyReconciliation(environment: ReturnType<typeof localFixtureEnvironment>, rawPool: Pool): Promise<void> {
  await rawPool.query({ text: "CREATE DATABASE platformsmoke" });
  const targetPool = new Pool({ host: environment.host, port: environment.port, database: "platformsmoke", user: "postgres", password: environment.password, max: 1, connectionTimeoutMillis: 5_000, ssl: false });
  let client: PoolClient | undefined;
  try {
    // Pool.query releases an errored client, losing its transaction. This
    // intentional SQL rejection and its recovery must share one checked-out client.
    client = await targetPool.connect();
    await client.query({ text: "DO $$ BEGIN CREATE ROLE psmokemigrate LOGIN PASSWORD 'fixture-migration-password'; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await client.query({ text: "DO $$ BEGIN CREATE ROLE psmokeruntime LOGIN PASSWORD 'fixture-runtime-password'; EXCEPTION WHEN duplicate_object THEN NULL; END $$" });
    await client.query({ text: "GRANT CONNECT, CREATE, TEMPORARY ON DATABASE platformsmoke TO psmokemigrate" });
    await client.query({ text: "GRANT CONNECT ON DATABASE platformsmoke TO psmokeruntime" });
    await client.query({ text: "GRANT psmokemigrate TO CURRENT_USER" });
    await client.query({ text: "CREATE SCHEMA platform_smoke AUTHORIZATION psmokemigrate" });
    await client.query({ text: "SET ROLE psmokemigrate" });
    await client.query({ text: "CREATE TABLE platform_smoke.bootstrap_effects_probe (id text)" });
    await client.query({ text: "RESET ROLE" });
    await client.query({ text: "GRANT USAGE ON SCHEMA platform_smoke TO psmokeruntime" });
    await client.query({ text: "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA platform_smoke TO psmokeruntime" });
    integrationPhase = "bootstrap-reconciliation-read-only-start";
    await client.query({ text: "BEGIN TRANSACTION READ ONLY" });
    await client.query({ text: "SAVEPOINT expected_write_rejection" });
    integrationPhase = "bootstrap-reconciliation-write-rejection";
    let writeRejected = false;
    try {
      await client.query({ text: "CREATE TABLE platform_smoke.read_only_must_reject (id text)" });
    } catch {
      writeRejected = true;
    }
    equal(writeRejected, true, "The reconciliation transaction must reject a database write.");
    integrationPhase = "bootstrap-reconciliation-savepoint-recovery";
    await client.query({ text: "ROLLBACK TO SAVEPOINT expected_write_rejection" });
    const readOnly = await client.query<{ transaction_read_only: string }>({ text: "SHOW transaction_read_only" });
    equal(readOnly.rows[0]?.transaction_read_only, "on", "Reconciliation must remain inside the same read-only transaction after rejection.");
    integrationPhase = "bootstrap-reconciliation-read-facts";
    const result = await client.query<Record<string, boolean>>({
      text: "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'psmokemigrate') AS migration_role_exists, EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'psmokeruntime') AS runtime_role_exists, pg_has_role(current_user, 'psmokemigrate', 'MEMBER') AS bootstrap_has_migration_membership, has_database_privilege('psmokemigrate', 'platformsmoke', 'CONNECT') AS migration_database_connect, has_database_privilege('psmokemigrate', 'platformsmoke', 'CREATE') AS migration_database_create, has_database_privilege('psmokemigrate', 'platformsmoke', 'TEMPORARY') AS migration_database_temporary, has_database_privilege('psmokeruntime', 'platformsmoke', 'CONNECT') AS runtime_database_connect, EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'platform_smoke') AS schema_exists, EXISTS (SELECT 1 FROM pg_namespace n JOIN pg_roles r ON r.oid = n.nspowner WHERE n.nspname = 'platform_smoke' AND r.rolname = 'psmokemigrate') AS schema_owned_by_migration, has_schema_privilege('psmokeruntime', 'platform_smoke', 'USAGE') AS runtime_schema_usage, NOT has_schema_privilege('psmokeruntime', 'platform_smoke', 'CREATE') AS runtime_schema_create_restricted, COALESCE((SELECT bool_and(has_table_privilege('psmokeruntime', c.oid, 'SELECT, INSERT, UPDATE, DELETE')) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'platform_smoke' AND c.relkind IN ('r','p','v','m','f')), true) AS runtime_existing_table_dml",
    });
    await client.query({ text: "ROLLBACK" });
    equal(result.rows.length, 1, "The fixed reconciliation query must return exactly one allowlisted fact set.");
    equal(Object.values(result.rows[0] ?? {}).every((value) => value === true), true, "The provisioned roles, grants, ownership, and restrictions must be recognized.");
  } finally {
    client?.release();
    await targetPool.end();
  }
}

function localFixtureEnvironment(): { readonly host: string; readonly port: number; readonly database: string; readonly password: string } {
  const host = process.env["POSTGRESQL_INTEGRATION_HOST"];
  const port = Number(process.env["POSTGRESQL_INTEGRATION_PORT"]);
  const database = process.env["POSTGRESQL_INTEGRATION_DATABASE"];
  const password = process.env["POSTGRESQL_INTEGRATION_PASSWORD"] ?? passwordFromFixtureFile(process.env["POSTGRESQL_INTEGRATION_PASSWORD_FILE"]);
  if (host === undefined || !Number.isInteger(port) || port < 1 || database === undefined || password === undefined || password.length === 0) {
    throw new Error("The disposable PostgreSQL fixture environment is incomplete.");
  }
  return { host, port, database, password };
}

function passwordFromFixtureFile(path: string | undefined): string | undefined {
  if (path === undefined) return undefined;
  const match = /^POSTGRES_PASSWORD=([^\r\n]+)\r?\n?$/.exec(readFileSync(path, "utf8"));
  return match?.[1];
}

function at(seconds: number): ISODateTime {
  return isoDateTimeFromDate(new Date(fixtureStart.getTime() + (seconds * 1_000)));
}

function testMutation(recordValue: string, occurredAt: ISODateTime, syntheticTenant: string) {
  const record = recordReference({
    kind: required(recordKind("platform-smoke.work-item")),
    id: required(recordId(recordValue)),
  });
  const change = required(recordChange({
    id: recordChangeId(`synthetic-change-${recordValue}`),
    record,
    revision: required(recordRevision(1)),
    action: "created",
    occurredAt,
    tenantId: tenantId(syntheticTenant),
    causationId: causationId(`synthetic-cause-${recordValue}`),
  }));
  return required(platformPersistenceMutation({
    recordChange: change,
    outboxEntry: outboxEntry({
      id: outboxEntryId(`synthetic-outbox-${recordValue}`),
      subject: record,
      messageType: required(outboxMessageType("platform-smoke.work-item.accepted")),
      deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")),
      createdAt: occurredAt,
      tenantId: tenantId(syntheticTenant),
      causationId: causationId(`synthetic-cause-${recordValue}`),
    }),
  }));
}

function claimedFence(result: Awaited<ReturnType<ReturnType<typeof createPostgreSqlPlatformOutboxStore>["claim"]>> | Awaited<ReturnType<ReturnType<typeof createPostgreSqlPlatformProcessingStore>["claim"]>>) {
  if (!result.ok || result.value.disposition !== "claimed" || result.value.record.lease === undefined) {
    throw new Error("The fixture expected a successful active claim.");
  }
  return result.value.record.lease.fence;
}

function inMemoryQueue(): Queue<PlatformOutboxQueuePayload> & { readonly messages: QueueMessage<PlatformOutboxQueuePayload>[] } {
  const messages: QueueMessage<PlatformOutboxQueuePayload>[] = [];
  return {
    messages,
    async send(message) {
      messages.push(message);
      return ok(undefined);
    },
  };
}

async function count(pool: Pool, text: string, values?: readonly unknown[]): Promise<number> {
  const result = await pool.query<{ readonly count: number }>({ text, ...(values === undefined ? {} : { values: [...values] }) });
  const row = result.rows[0];
  if (row === undefined) throw new Error("The fixture count query returned no row.");
  return Number(row.count);
}

function required<TValue>(result: { readonly ok: true; readonly value: TValue } | { readonly ok: false }): TValue {
  if (!result.ok) throw new Error("A fixed disposable PostgreSQL fixture value was invalid.");
  return result.value;
}

main().catch(() => {
  console.error(`PostgreSQL disposable integration proof failed safely during ${integrationPhase}.`);
  process.exitCode = 1;
});

async function diagnosticEngineFailures(environment: { host: string; port: number; database: string; password: string }): Promise<void> {
  const options = { host: environment.host, port: environment.port, database: environment.database, user: "postgres", password: environment.password, ssl: false as const, connectionTimeoutMillis: 1_000 };
  for (const [override, classification, codeStatus] of [[{ password: "synthetic-wrong-password" }, "authentication_rejected", "recognized"], [{ database: "synthetic_absent_database" }, "content_unavailable", "recognized"], [{ password: async () => undefined as unknown as string }, "authentication_material_invalid", "absent"]] as const) {
    integrationPhase = `diagnostic-${classification}`;
    const pool = nodePoolAdapter(new Pool({ ...options, ...override }));
    try {
      let failure: unknown;
      try { const client = await pool.connect(); client.release(); } catch (error) { failure = error; }
      const diagnostic = postgreSqlFailureDiagnostic(failure);
      // Emit the already allowlisted diagnostic descriptor, not the provider
      // error. This makes a hosted-fixture disagreement actionable without
      // leaking a password, host, SQLSTATE message, or connection string.
      console.log(JSON.stringify({
        event: "postgresql-disposable-diagnostic-observed",
        scenario: classification,
        facts: diagnostic.facts,
        connection_rejected: failure !== undefined,
      }));
      equal(diagnostic.facts.classification, classification);
      equal(diagnostic.facts.phase, "pool_connect"); equal(diagnostic.facts.code_status, codeStatus);
      assertOk(diagnostic.facts.elapsed_ms !== null && diagnostic.facts.elapsed_ms >= 0);
      equal(JSON.stringify(diagnostic).includes(environment.password), false);
      equal(JSON.stringify(diagnostic).includes("SASL:"), false);
      if (classification === "authentication_material_invalid") equal(diagnostic.failureKind, "configuration");
    } finally { await pool.end(); }
  }
  integrationPhase = "diagnostic-query-timeout";
  const pool = nodePoolAdapter(new Pool({ ...options, options: "-c statement_timeout=50" }));
  try {
    const client = await pool.connect();
    try {
      let failure: unknown;
      try { await client.query({ text: "SELECT pg_sleep(0.2)" }); } catch (error) { failure = error; }
      const diagnostic = postgreSqlFailureDiagnostic(failure);
      equal(diagnostic.facts.classification, "query_canceled"); equal(diagnostic.facts.phase, "query");
      assertOk(diagnostic.facts.elapsed_ms !== null && diagnostic.facts.elapsed_ms >= 20);
    } finally { client.release(); }
  } finally { await pool.end(); }
  console.log("PostgreSQL disposable authentication, missing-database and query-timeout diagnostics passed.");
}
