import { deepEqual, equal, rejects } from "node:assert/strict";
import { ok, uuid, type ISODateTime } from "@kanbien/core/shared";
import { outboxDeliveryPolicy, outboxEntry, outboxEntryId, outboxMessageType, recordId, recordKind, recordReference } from "@kanbien/core/persistence";
import { platformJobName } from "@kanbien/platform-contracts";
import {
  createPlatformSchedule,
  persistenceScheduleStoreRejectionDiagnosticRecord,
  persistenceScheduleStoredRecordDiagnosticRecord,
  persistenceScheduleSubjectDiagnosticRecord,
  persistenceScheduleInvalidRowBlockedDiagnosticRecord,
  createPlatformScheduleDelivery, createPlatformScheduleDispatcher,
} from "@kanbien/platform-persistence";
import {
  createPostgreSqlPlatformScheduleStore,
  postgreSqlPersistenceConfiguration,
  postgreSqlPlatformScheduleHandoffMigration,
  postgreSqlPlatformScheduleMigration,
  postgreSqlPlatformScheduleSubjectMigration,
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
const row = { id: String(schedule.id), job_name: String(schedule.jobName), due_at: new Date(schedule.dueAt), state: "waiting", outbox_entry_id: null, subject_kind: null, subject_id: null };
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
  equal(statements[0]?.text, 'INSERT INTO "platform_smoke"."platform_schedule" (id, job_name, due_at, state, subject_kind, subject_id) VALUES ($1, $2, $3, $4, $5, $6) RETURNING id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id');
  deepEqual(statements[0]?.values, [schedule.id, schedule.jobName, schedule.dueAt, "waiting", null, null]);
  equal(statements[1]?.text, 'SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM "platform_smoke"."platform_schedule" WHERE id = $1');
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
    'SELECT id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id FROM "platform_smoke"."platform_schedule" WHERE id = $1 FOR UPDATE',
    'INSERT INTO "platform_smoke"."platform_outbox" (id, subject_kind, subject_id, message_type, message_version, delivery_policy, created_at, tenant_id, correlation_id, causation_id, state, attempt) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, \'pending\', 0)',
    'UPDATE "platform_smoke"."platform_schedule" SET state = \'delivery-created\', outbox_entry_id = $2 WHERE id = $1 RETURNING id, job_name, due_at, state, outbox_entry_id, subject_kind, subject_id',
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
  const subjectMigration = postgreSqlPlatformScheduleSubjectMigration("platform_smoke", "v0005_platform_schedule_subject");
  equal(subjectMigration.id, "v0005_platform_schedule_subject");
  equal(subjectMigration.statements.length, 2);
  equal(subjectMigration.statements[0]?.text, 'ALTER TABLE "platform_smoke"."platform_schedule" ADD COLUMN subject_kind text, ADD COLUMN subject_id text');
  await subjectRoundTripAndRejections();
  await invalidDueIsolationAndRepair();
}

async function invalidDueIsolationAndRepair(): Promise<void> {
  const invalid = { ...row, id: "a1d06aac-3d17-4292-b9f3-1fe370772a5d", job_name: "PRIVATE INVALID JOB" };
  const statements: PostgreSqlStatement[] = [];
  const records: unknown[] = [];
  let committed = false;
  const store = createPostgreSqlPlatformScheduleStore({ configuration, onDiagnostic(record) {
    records.push(record);
    if (record.code === "persistence.schedule-invalid-row-blocked") equal(committed, true, "blocking is reported only after commit");
    throw new Error("PRIVATE-SINK-FAILURE");
  }, pool: transactionPool(async statement => {
    statements.push(statement);
    if (statement.text === "COMMIT") { committed = true; return { rows: [] }; }
    if (statement.text === "BEGIN") { committed = false; return { rows: [] }; }
    if (statement.text.includes("SKIP LOCKED")) return { rows: [invalid, row] };
    if (statement.text.includes("SET state = 'blocked-invalid-row'")) return { rows: [{ id: invalid.id }], rowCount: 1 };
    if (statement.text.includes("FOR UPDATE")) return { rows: [row] };
    if (statement.text.startsWith("INSERT")) return { rows: [] };
    if (statement.text.includes("SET state = 'delivery-created'")) return { rows: [{ ...row, state: "delivery-created", outbox_entry_id: String(outbox.id) }] };
    throw new Error("Unexpected bounded isolation statement.");
  }) });
  let relayCalls = 0;
  const result = required(await createPlatformScheduleDispatcher({
    delivery: createPlatformScheduleDelivery({ clock: { now: () => new Date(schedule.dueAt) }, scheduleStore: store, maximumSchedules: 2,
      createOutboxEntry: () => outbox }),
    relay: { runOnce: async () => { relayCalls++; return ok({ status: "idle" as const }); } }, maximumRelayAttempts: 1,
  }).runOnce());
  equal(result.delivery?.deliveryCreated, 1, "the healthy selected row progresses past an invalid older row");
  equal(relayCalls, 1, "older outbox work still receives a relay opportunity");
  deepEqual(statements.find(statement => statement.text.includes("SKIP LOCKED"))?.values, [schedule.dueAt, 2]);
  deepEqual(statements.find(statement => statement.text.includes("SET state = 'blocked-invalid-row'"))?.values, [[invalid.id]]);
  equal(records.some(record => JSON.stringify(record) === JSON.stringify(persistenceScheduleInvalidRowBlockedDiagnosticRecord())), true);
  equal(JSON.stringify(records).includes("PRIVATE"), false);

  const invalidPage = Array.from({ length: 100 }, (_, index) => ({ ...invalid,
    id: `a1d06aac-3d17-4292-b9f3-${String(index).padStart(12, "0")}` }));
  for (const fault of ["none", "duplicate-returned-id", "wrong-returned-id", "short-row-count"] as const) {
    const sql: PostgreSqlStatement[] = [];
    const page = await createPostgreSqlPlatformScheduleStore({ configuration, pool: transactionPool(async statement => {
      sql.push(statement);
      if (["BEGIN", "COMMIT", "ROLLBACK"].includes(statement.text)) return { rows: [] };
      if (statement.text.includes("SKIP LOCKED")) return { rows: invalidPage };
      const rows = invalidPage.map(row => ({ id: row.id }));
      if (fault === "duplicate-returned-id") rows[0] = rows[1]!;
      if (fault === "wrong-returned-id") rows[0] = { id: row.id };
      return { rows, rowCount: fault === "short-row-count" ? 99 : 100 };
    }) }).listDue({ asOf: schedule.dueAt, limit: 100, blockInvalid: true });
    equal(page.ok, fault === "none");
    equal(sql.length, 4, "a full invalid page has a fixed number of database round trips");
    const updates = sql.filter(statement => statement.text.startsWith("UPDATE"));
    equal(updates.length, 1);
    equal(updates[0]?.text.includes("id = ANY($1::uuid[])"), true);
    deepEqual(updates[0]?.values, [invalidPage.map(row => row.id)]);
    equal(sql.at(-1)?.text, fault === "none" ? "COMMIT" : "ROLLBACK");
  }

  for (const fault of ["update-no-match", "update-threw", "commit-threw", "invalid-id"] as const) {
    const seen: unknown[] = [], sql: string[] = [];
    const failed = await createPostgreSqlPlatformScheduleStore({ configuration, onDiagnostic: record => seen.push(record), pool: transactionPool(async statement => {
      sql.push(statement.text);
      if (statement.text === "BEGIN" || statement.text === "ROLLBACK") return { rows: [] };
      if (statement.text === "COMMIT") { if (fault === "commit-threw") throw new Error("PRIVATE-COMMIT"); return { rows: [] }; }
      if (statement.text.includes("SKIP LOCKED")) return { rows: [fault === "invalid-id" ? { ...invalid, id: "PRIVATE-ID" } : invalid] };
      if (fault === "update-threw") throw new Error("PRIVATE-UPDATE");
      return { rows: fault === "update-no-match" ? [] : [{ id: invalid.id }], rowCount: fault === "update-no-match" ? 0 : 1 };
    }) }).listDue({ asOf: schedule.dueAt, limit: 1, blockInvalid: true });
    equal(failed.ok, false);
    equal(seen.some(record => (record as { code: string }).code === "persistence.schedule-invalid-row-blocked"), false);
    if (fault !== "commit-threw") equal(sql.includes("ROLLBACK"), true);
  }

  for (const repaired of [false, true]) {
    const sql: string[] = [];
    const resumed = await createPostgreSqlPlatformScheduleStore({ configuration, pool: transactionPool(async statement => {
      sql.push(statement.text);
      if (["BEGIN", "COMMIT", "ROLLBACK"].includes(statement.text)) return { rows: [] };
      if (statement.text.includes("FOR UPDATE")) return { rows: [{ ...(repaired ? row : invalid), state: "blocked-invalid-row" }] };
      return { rows: [{ ...row, state: "waiting" }] };
    }) }).resumeBlocked(schedule.id);
    equal(resumed.ok, repaired);
    equal(sql.some(statement => statement.startsWith("UPDATE")), repaired, "unrepaired rows cannot be released by a failed resume");
    equal(sql.at(-1), repaired ? "COMMIT" : "ROLLBACK");
  }

  let reads = 0;
  const pure = await createPostgreSqlPlatformScheduleStore({ configuration, pool: pool(async () => { reads++; return { rows: [invalid, row] }; }) })
    .listDue({ asOf: schedule.dueAt, limit: 2 });
  equal(pure.ok, false, "ordinary scans remain read-only and fail closed"); equal(reads, 1);
}

async function subjectRoundTripAndRejections(): Promise<void> {
  const subject = recordReference({ kind: required(recordKind("fixture.test-entity")), id: required(recordId("private-entity-identity")) });
  const targeted = { ...schedule, subject };
  const targetedRow = { ...row, subject_kind: subject.kind, subject_id: subject.id };
  const statements: PostgreSqlStatement[] = [];
  const store = createPostgreSqlPlatformScheduleStore({ configuration, pool: pool(async statement => {
    statements.push(statement); return { rows: [targetedRow] };
  }) });
  deepEqual(await store.create(targeted), { ok: true, value: targeted });
  deepEqual(await store.get(targeted.id), targeted);
  deepEqual(await store.listDue({ asOf: targeted.dueAt, limit: 1 }), { ok: true, value: [targeted] });
  deepEqual(statements[0]?.values, [schedule.id, schedule.jobName, schedule.dueAt, "waiting", subject.kind, subject.id]);

  const invalid: readonly [unknown, unknown, "subject-kind" | "subject-id" | "subject-pair", "invalid" | "partial"][] = [
    [null, subject.id, "subject-pair", "partial"], [subject.kind, null, "subject-pair", "partial"],
    [undefined, undefined, "subject-kind", "invalid"], [17, subject.id, "subject-kind", "invalid"],
    ["INVALID PRIVATE KIND", subject.id, "subject-kind", "invalid"], [subject.kind, 17, "subject-id", "invalid"],
    [subject.kind, "", "subject-id", "invalid"], [subject.kind, " PRIVATE ID ", "subject-id", "invalid"],
  ];
  for (const [kind, id, field, condition] of invalid) {
    const observations: unknown[] = [];
    const invalidStore = createPostgreSqlPlatformScheduleStore({ configuration,
      pool: pool(async () => ({ rows: [{ ...row, subject_kind: kind, subject_id: id }] })),
      onDiagnostic(record) { observations.push(record); throw new Error("PRIVATE-REPORTER-FAULT"); },
    });
    const expected = persistenceScheduleSubjectDiagnosticRecord({ operation: "read", effect: "not-assessed", field, condition });
    await rejects(() => invalidStore.get(schedule.id), error => {
      deepEqual((error as { diagnosticRecord: unknown }).diagnosticRecord, expected); return true;
    });
    deepEqual(observations, [expected]);
    equal(JSON.stringify(observations).includes("PRIVATE"), false);
    equal(JSON.stringify(observations).includes("private-entity"), false);
  }
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
