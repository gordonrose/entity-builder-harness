import { deepEqual, equal, rejects } from "node:assert/strict";
import { uuid, type ISODateTime } from "@kanbien/core/shared";
import { outboxDeliveryPolicy, outboxEntry, outboxEntryId, outboxMessageType, recordId, recordKind, recordReference } from "@kanbien/core/persistence";
import { platformJobName } from "@kanbien/platform-contracts";
import {
  createPlatformSchedule,
  persistenceScheduleStoreRejectionDiagnosticRecord,
  persistenceScheduleStoredRecordDiagnosticRecord,
} from "@kanbien/platform-persistence";
import {
  createPostgreSqlPlatformScheduleStore,
  postgreSqlPersistenceConfiguration,
  postgreSqlPlatformScheduleHandoffMigration,
  postgreSqlPlatformScheduleMigration,
  type PostgreSqlConnectionPool,
  type PostgreSqlStatement,
} from "../../src/index";

const configuration = required(postgreSqlPersistenceConfiguration({
  host: "postgres.internal.example", port: 5432, database: "platform_smoke", schema: "platform_smoke",
  runtimeCredentialSecretReference: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:platform-smoke-runtime",
  maximumPoolSize: 4, connectionTimeoutMs: 1_000, idleTimeoutMs: 10_000, statementTimeoutMs: 5_000,
  tls: { mode: "verify-full", certificateAuthoritySource: "injected" },
}));
const jobName = required(platformJobName("entity-smoke.test-entity.purge-expired"));
const schedule = required(createPlatformSchedule({ jobName, dueAt: "2026-09-23T13:30:00+01:00" }, {
  generate: () => uuid("e1d06aac-3d17-4292-b9f3-1fe370772a5d"),
}));
const row = { id: String(schedule.id), job_name: String(schedule.jobName), due_at: new Date(schedule.dueAt), state: "waiting", outbox_entry_id: null };
const outbox = outboxEntry({ id: outboxEntryId("schedule-handoff-1"), subject: recordReference({ kind: required(recordKind("platform.schedule")), id: required(recordId(String(schedule.id))) }),
  messageType: required(outboxMessageType("platform.schedule.due")), deliveryPolicy: required(outboxDeliveryPolicy("platform-short-idempotent-work.v1")), createdAt: schedule.dueAt });

async function main(): Promise<void> {
  const statements: PostgreSqlStatement[] = [];
  const store = createPostgreSqlPlatformScheduleStore({ configuration, pool: pool(async statement => {
    statements.push(statement);
    return { rows: [row] };
  }) });
  deepEqual(await store.create(schedule), { ok: true, value: schedule });
  deepEqual(await store.get(schedule.id), schedule);
  equal(statements.length, 2);
  equal(statements[0]?.text, 'INSERT INTO "platform_smoke"."platform_schedule" (id, job_name, due_at, state) VALUES ($1, $2, $3, $4) RETURNING id, job_name, due_at, state, outbox_entry_id');
  deepEqual(statements[0]?.values, [schedule.id, schedule.jobName, schedule.dueAt, "waiting"]);
  equal(statements[1]?.text, 'SELECT id, job_name, due_at, state, outbox_entry_id FROM "platform_smoke"."platform_schedule" WHERE id = $1');
  deepEqual(statements[1]?.values, [schedule.id]);

  const duplicateRecords: unknown[] = [];
  const duplicate = await createPostgreSqlPlatformScheduleStore({ configuration, pool: pool(async () => { throw { code: "23505" }; }), onDiagnostic: record => duplicateRecords.push(record) }).create(schedule);
  equal(duplicate.ok, false);
  if (!duplicate.ok) {
    equal(duplicate.error.code, "PLATFORM_PERSISTENCE_DUPLICATE_SCHEDULE");
    deepEqual(duplicate.error.diagnosticRecord, persistenceScheduleStoreRejectionDiagnosticRecord({ operation: "create", field: "id", condition: "duplicate", effect: "unknown" }));
  }
  deepEqual(duplicateRecords, [persistenceScheduleStoreRejectionDiagnosticRecord({ operation: "create", field: "id", condition: "duplicate", effect: "unknown" })]);

  const invalidRecords: unknown[] = [];
  await rejects(() => createPostgreSqlPlatformScheduleStore({ configuration, pool: pool(async () => ({ rows: [{ ...row, state: "delivered" }] })), onDiagnostic: record => invalidRecords.push(record) }).get(schedule.id), error => {
    deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, persistenceScheduleStoredRecordDiagnosticRecord({ operation: "read", reduction: "returned", effect: "not-assessed", field: "state", condition: "invalid" }));
    return true;
  });
  deepEqual(invalidRecords, [persistenceScheduleStoredRecordDiagnosticRecord({ operation: "read", reduction: "returned", effect: "not-assessed", field: "state", condition: "invalid" })]);

  const handoffStatements: PostgreSqlStatement[] = [];
  const deliveredRow = { ...row, state: "delivery-created", outbox_entry_id: String(outbox.id) };
  const handedOver = await createPostgreSqlPlatformScheduleStore({ configuration, pool: transactionPool(async statement => {
    handoffStatements.push(statement);
    if (statement.text === "BEGIN" || statement.text === "COMMIT") return { rows: [] };
    if (statement.text.includes("FOR UPDATE")) return { rows: [row] };
    if (statement.text.startsWith("INSERT INTO \"platform_smoke\".\"platform_outbox\"")) return { rows: [] };
    if (statement.text.startsWith("UPDATE \"platform_smoke\".\"platform_schedule\"")) return { rows: [deliveredRow] };
    throw new Error("Unexpected handoff statement.");
  }) }).handoverDue({ scheduleId: schedule.id, asOf: schedule.dueAt, outboxEntry: outbox });
  equal(handedOver.ok, true);
  if (!handedOver.ok || handedOver.value.disposition !== "outbox-created") throw new Error("Expected one atomic outbox handoff.");
  equal(handedOver.value.schedule.state, "delivery-created");
  equal(handedOver.value.schedule.outboxEntryId, outbox.id);
  deepEqual(handoffStatements.map(statement => statement.text), [
    "BEGIN",
    'SELECT id, job_name, due_at, state, outbox_entry_id FROM "platform_smoke"."platform_schedule" WHERE id = $1 FOR UPDATE',
    'INSERT INTO "platform_smoke"."platform_outbox" (id, subject_kind, subject_id, message_type, message_version, delivery_policy, created_at, tenant_id, correlation_id, causation_id, state, attempt) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, \'pending\', 0)',
    'UPDATE "platform_smoke"."platform_schedule" SET state = \'delivery-created\', outbox_entry_id = $2 WHERE id = $1 RETURNING id, job_name, due_at, state, outbox_entry_id',
    "COMMIT",
  ]);
  deepEqual(handoffStatements[2]?.values, [outbox.id, outbox.subject.kind, outbox.subject.id, outbox.messageType, outbox.messageVersion, outbox.deliveryPolicy, outbox.createdAt, null, null, null]);

  const migration = postgreSqlPlatformScheduleMigration("platform_smoke", "v0003_platform_schedule");
  equal(migration.id, "v0003_platform_schedule");
  equal(migration.statements.length, 1);
  equal(migration.statements[0]?.text, 'CREATE TABLE IF NOT EXISTS "platform_smoke"."platform_schedule" (id uuid PRIMARY KEY, job_name text NOT NULL, due_at timestamptz NOT NULL, state text NOT NULL CHECK (state = \'waiting\'))');
  const handoffMigration = postgreSqlPlatformScheduleHandoffMigration("platform_smoke", "v0004_platform_schedule_handoff");
  equal(handoffMigration.statements.length, 5);
  equal(handoffMigration.statements[3]?.text, 'ALTER TABLE "platform_smoke"."platform_schedule" ADD CONSTRAINT platform_schedule_outbox_entry_id_fkey FOREIGN KEY (outbox_entry_id) REFERENCES "platform_smoke"."platform_outbox" (id)');
}

function transactionPool(respond: (statement: PostgreSqlStatement) => Promise<{ readonly rows: readonly unknown[] }>): PostgreSqlConnectionPool {
  const client = { query: async (statement: PostgreSqlStatement) => respond(statement) as never, release: () => undefined };
  return { query: async () => { throw new Error("Handoff must use one transaction."); }, connect: async () => client, end: async () => undefined };
}

function pool(respond: (statement: PostgreSqlStatement) => Promise<{ readonly rows: readonly unknown[] }>): PostgreSqlConnectionPool {
  return {
    query: async statement => respond(statement) as never,
    connect: async () => { throw new Error("The schedule store never opens a transaction."); },
    end: async () => undefined,
  };
}
function required<T>(result: { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: unknown }): T {
  if (!result.ok) throw result.error;
  return result.value;
}

void main();
