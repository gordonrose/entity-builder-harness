import { equal } from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Pool } from "pg";
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
import type { Queue, QueueMessage } from "@kanbien/core/queues";
import { causationId, err, isoDateTimeFromDate, type ISODateTime, ok } from "@kanbien/core/shared";
import { tenantId } from "@kanbien/core/tenancy";
import {
  createPlatformOutboxRelay,
  platformPersistenceError,
  platformPersistenceLeaseOwner,
  platformPersistenceMutation,
  type PlatformOutboxQueuePayload,
} from "@kanbien/platform-persistence";
import { acceptPlatformSmokeWorkItem, platformSmokeWorkItemId } from "../../../../../../apps/platform-smoke/src/persistence/index";
import {
  createKanbienPlatformPostgreSqlSmokePersistence,
  kanbienPlatformSmokePostgreSqlMigration,
} from "../../../../../../infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-persistence";
import {
  createPostgreSqlMigrationRunner,
  createPostgreSqlPlatformOutboxStore,
  createPostgreSqlPlatformProcessingStore,
  postgreSqlPersistenceConfiguration,
  postgreSqlPersistenceFoundationMigration,
  stagePostgreSqlTransactionStatement,
} from "../src/index";
import { nodePoolAdapter } from "../src/connection";

const schema = "platform_smoke";
const fixtureStart = new Date("2026-09-26T12:00:00.000Z");

async function main(): Promise<void> {
  const environment = localFixtureEnvironment();
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
    const migrations = [foundationMigration, smokeMigration];
    const migrationRunner = createPostgreSqlMigrationRunner(configuration, { pool }, "stage3-local");
    console.log("PostgreSQL disposable assertion phase: immutable migrations.");
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
    equal(await count(rawPool, `SELECT COUNT(*)::integer AS count FROM "${schema}"."platform_migration_history"`), 2);

    const smokePersistence = createKanbienPlatformPostgreSqlSmokePersistence({
      configuration,
      pool,
      telemetry: (observation) => telemetry.push(observation),
    });
    const atomicWorkItemId = required(platformSmokeWorkItemId("synthetic-work-item-atomic"));
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

    console.log("PostgreSQL disposable assertion phase: telemetry safety.");
    const telemetryText = JSON.stringify(telemetry);
    equal(telemetryText.includes(environment.password), false, "Normal telemetry must not contain the fixture password.");
    equal(telemetryText.includes("synthetic-tenant-a"), false, "Normal telemetry must not contain a tenant identifier.");
    console.log("PostgreSQL disposable integration proof passed.");
  } finally {
    await rawPool.end();
  }
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
  console.error("PostgreSQL disposable integration proof failed.");
  process.exitCode = 1;
});
