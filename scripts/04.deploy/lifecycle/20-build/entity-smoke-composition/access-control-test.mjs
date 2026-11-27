// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.access-control
//   version: 5
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Exercise fixed-identity access revocation and restoration, safe observations and no replay with controlled database responses.
//   portability: {class: internal, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.test.entity-smoke.composition.wrapper
//     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
const require = createRequire(import.meta.url);
const root = resolve(process.argv[2]);
const { performEntitySmokeAdministration, runEntitySmokeAdministration, entitySmokeSchedulingDatabasePolicy } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/administration.js"));
const { observeSchedulingDatabaseState, observeSchedulingMigrationPrefix, grantSchedulingDatabaseAccess, proveSchedulingDatabaseAccess } = require(join(root, "infra/04.deploy/03.product/entrypoints/shared/persistence/scheduling-administration.js"));
const { entitySmokePasswordAuthenticationPredicate } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/preflight.js"));
const { reportEntitySmokeFailure } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js"));
const canary = "private-session-and-credential-canary";
for (const operation of ["grant-scheduling-access", "observe-scheduling-state", "prove-scheduling-access", "observe-scheduling-prefix"]) {
  const pool = { query() { assert.fail("new scheduler operations must not fall through the legacy runtime-grant implementation"); }, connect() { assert.fail("unsupported legacy dispatch must reject before connecting"); } };
  await assert.rejects(() => performEntitySmokeAdministration(pool, operation, "entityfixture"), error => error.diagnosticRecord?.detail?.field === "operation");
}
const schedulingPolicy = entitySmokeSchedulingDatabasePolicy("entityfixture");
assert.equal(schedulingPolicy.manifest.continuation.minimumAppliedMigrations, 1, "accepted Entity history is one migration, not the current four-entry baseline");
const migrationPairs = schedulingPolicy.manifest.migrations.map(({ id, checksum }) => ({ id, checksum }));
const digest = value => createHash("sha256").update(JSON.stringify(value)).digest("hex");
{
  const connection = require(join(root, "platform/adapters/aws/persistence/postgresql/src/connection.js"));
  const configuration = require(join(root, "infra/04.deploy/03.product/entrypoints/shared/persistence/configuration.js"));
  const originalPool = connection.createNodePostgreSqlConnectionPool, originalAuthority = configuration.persistenceCertificateAuthorityResult;
  const originalLog = console.log, originalError = console.error, originalExit = process.exitCode;
  try {
    configuration.persistenceCertificateAuthorityResult = () => ({ ok: true, value: "controlled-certificate" });
    for (const applied of [0, 1, 4, 7]) for (const cleanupFails of [false, true]) {
      const statements = [], output = [], current = schedulingStateFixture(undefined, statements, migrationPairs.slice(0, applied).map(({ id, checksum }) => ({ migration_id: id, checksum })));
      current.pool.end = async () => { statements.push("end"); if (cleanupFails) throw new Error(canary); };
      connection.createNodePostgreSqlConnectionPool = () => current.pool;
      console.log = console.error = line => { statements.push("output"); output.push(JSON.parse(line)); }; process.exitCode = undefined;
      await runEntitySmokeAdministration({ ENTITY_SMOKE_ADMINISTRATION_OPERATION: "observe-scheduling-prefix", PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432",
        PERSISTENCE_POSTGRES_DATABASE: schedulingPolicy.database, PERSISTENCE_POSTGRES_SCHEMA: "entity_smoke", PERSISTENCE_RUNTIME_DATABASE_USERNAME: schedulingPolicy.httpUsername,
        PERSISTENCE_MIGRATION_DATABASE_USERNAME: schedulingPolicy.migrationUsername, PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/rds-eu-west-1-bundle.crt",
        PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:synthetic-administrator",
        PERSISTENCE_ADMINISTRATOR_CREDENTIALS: JSON.stringify({ username: "fixture_administrator", password: "controlled-password" }) });
      assert.equal(current.released(), 1);
      if (applied > 0 && !cleanupFails) {
        assert.deepEqual(output, [{ verdict: "passed", operation: "observe-scheduling-prefix", code: "PERSISTENCE_SCHEDULING_PREFIX_CONFIRMED", migration_prefix: {
          schema: "kanbien/scheduling-migration-prefix/v1", manifest_sha256: digest(migrationPairs), manifest_migration_count: 7,
          minimum_applied_migrations: 1, applied_migrations: applied, applied_prefix_sha256: digest(migrationPairs.slice(0, applied)), state: applied === 7 ? "complete" : "partial" } }]);
        assert(statements.indexOf("output") > statements.indexOf("end"));
      } else { assert.equal(process.exitCode, 1); assert(!output.some(item => item.verdict === "passed")); }
      assert(!JSON.stringify(output).includes(canary));
    }
  } finally { connection.createNodePostgreSqlConnectionPool = originalPool; configuration.persistenceCertificateAuthorityResult = originalAuthority;
    console.log = originalLog; console.error = originalError; process.exitCode = originalExit; }
}
for (const applied of [1, 4, 7]) {
  const statements = [], history = migrationPairs.slice(0, applied).map(({ id, checksum }) => ({ migration_id: id, checksum }));
  const current = schedulingStateFixture(undefined, statements, history);
  const result = await observeSchedulingMigrationPrefix(current.pool, schedulingPolicy);
  assert.deepEqual(result, { schema: "kanbien/scheduling-migration-prefix/v1", manifest_sha256: digest(migrationPairs), manifest_migration_count: 7,
    minimum_applied_migrations: 1, applied_migrations: applied, applied_prefix_sha256: digest(migrationPairs.slice(0, applied)), state: applied === 7 ? "complete" : "partial" });
  assert(!statements.some(text => /platform_schedule|platform_outbox|platform_processing|test_entity|pg_proc|information_schema|^(INSERT|UPDATE|DELETE|ALTER|GRANT|CREATE|LOCK)/.test(text)), "partial prefix observation must not require scheduler or application tables");
  assert.equal(statements.at(-1), "COMMIT"); assert.equal(current.released(), 1);
}
for (const history of [[], [{ migration_id: canary, checksum: canary }], [{ migration_id: migrationPairs[0].id, checksum: canary }]]) {
  const statements = [], records = [], current = schedulingStateFixture(undefined, statements, history);
  await assert.rejects(() => observeSchedulingMigrationPrefix(current.pool, schedulingPolicy, { onObservation(record, source) { records.push({ record, source }); } }));
  assert.equal(statements.at(-1), "ROLLBACK"); assert.equal(current.released(), 1);
  assert(JSON.stringify(records).includes("persistence.local-rejected")); assert(!JSON.stringify(records).includes(canary));
}
for (const rows of [[], [{ owner: canary }], [{ owner: schedulingPolicy.migrationUsername }, { owner: schedulingPolicy.migrationUsername }]]) {
  const statements = [], records = [], current = schedulingStateFixture(undefined, statements);
  const connect = current.pool.connect;
  current.pool.connect = async () => {
    const client = await connect();
    return { ...client, query(statement) { if (statement.text.startsWith("SELECT pg_get_userbyid")) { statements.push(statement.text); return { rows }; } return client.query(statement); } };
  };
  await assert.rejects(() => observeSchedulingMigrationPrefix(current.pool, schedulingPolicy, { onObservation(record) { records.push(record); } }));
  assert.equal(statements.at(-1), "ROLLBACK"); assert.equal(current.released(), 1);
  assert(records.some(record => record.detail.field === "relation-name" && record.detail.condition === "predicate-rejected"));
  assert(!JSON.stringify(records).includes(canary));
}
for (const observer of [observeSchedulingDatabaseState, observeSchedulingMigrationPrefix]) for (const rows of [[], [{ acquired: false }], [{ acquired: "true" }], [{ acquired: 1 }], [{}], [null], [{ acquired: true }, { acquired: true }]]) {
  const statements = [], records = [];
  const current = schedulingStateFixture({}, statements, undefined, rows);
  await assert.rejects(() => observer(current.pool, schedulingPolicy, { onObservation(record) { records.push(record); throw new Error(canary); } }));
  assert.deepEqual(statements, ["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY", "SET LOCAL lock_timeout = '30000ms'", "SELECT pg_try_advisory_xact_lock(hashtext($1)) AS acquired", "ROLLBACK"]);
  assert.equal(current.released(), 1);
  assert(records.some(record => record.detail.operation === "migration-state" && record.detail.field === "row" && record.detail.condition === (rows.length === 1 ? "not-true" : "count-mismatch")));
  assert(!JSON.stringify(records).includes(canary));
}
for (const inventory of [
  { waiting_schedules: 0, pending_outbox: 0, active_processing: 0, ignored: canary },
  { waiting_schedules: -1, pending_outbox: 0, active_processing: 0 },
  { waiting_schedules: 0, pending_outbox: "0", active_processing: 0 },
  { waiting_schedules: 0, pending_outbox: 0, active_processing: 0.5 },
  undefined,
]) {
  const statements = [], records = [], fixture = schedulingStateFixture(inventory, statements);
  const promise = observeSchedulingDatabaseState(fixture.pool, schedulingPolicy, { onObservation(record) { records.push(record); throw new Error(canary); } });
  if (inventory?.ignored === canary) {
    const result = await promise;
    assert.deepEqual(result.work_inventory, { waiting_schedules: 0, pending_outbox: 0, active_processing: 0 });
    assert(!JSON.stringify(result).includes(canary));
  } else await assert.rejects(() => promise);
  assert(statements.includes("SET LOCAL statement_timeout = '5000ms'"));
  assert(statements.includes("SELECT pg_try_advisory_xact_lock(hashtext($1)) AS acquired"));
  assert(!statements.includes("SELECT pg_advisory_xact_lock(hashtext($1))"));
  assert(!statements.some(text => /^(INSERT|UPDATE|DELETE|ALTER|GRANT|CREATE)/.test(text)));
  assert(!JSON.stringify(records).includes(canary));
  assert.equal(fixture.released(), 1);
}
const cancelled = Object.assign(new Error(canary), { code: "57014" });
await assert.rejects(() => observeSchedulingDatabaseState(schedulingStateFixture(cancelled, []).pool, schedulingPolicy), error => error === cancelled);
for (const observer of [observeSchedulingDatabaseState, observeSchedulingMigrationPrefix]) {
  const statements = [], records = [], primary = new Error(canary), rollback = new Error(canary), release = new Error(canary);
  const current = schedulingStateFixture({}, statements, undefined, primary);
  const connect = current.pool.connect;
  current.pool.connect = async () => {
    const client = await connect();
    return { query(statement) { if (statement.text === "ROLLBACK") { statements.push(statement.text); throw rollback; } return client.query(statement); },
      release() { client.release(); throw release; } };
  };
  await assert.rejects(() => observer(current.pool, schedulingPolicy, { onObservation(record) { records.push(record); } }), error => error === primary);
  assert.equal(current.released(), 1);
  assert.deepEqual(records.filter(record => record.detail.condition === "threw").map(record => record.detail.phase), ["history-read", "rollback", "client-release"]);
  assert(!JSON.stringify(records).includes(canary));
}
for (const bodyFails of [false, true]) {
  const primary = new Error(canary), release = new Error(canary), records = [];
  const current = schedulingStateFixture(bodyFails ? primary : { waiting_schedules: 0, pending_outbox: 0, active_processing: 0 }, []);
  const connect = current.pool.connect;
  current.pool.connect = async () => ({ ...await connect(), release() { throw release; } });
  await assert.rejects(() => observeSchedulingDatabaseState(current.pool, schedulingPolicy, { onObservation(record) { records.push(record); throw new Error(canary); } }), error => error === (bodyFails ? primary : release));
  assert(records.some(record => record.detail.phase === "client-release"));
  if (bodyFails) assert(records.some(record => record.detail.phase === "runtime-read" && record.detail.field === "read-count"));
  assert(!JSON.stringify(records).includes(canary));
}
for (const scenario of ["body-and-pool-end", "pool-end", "body-and-probe-cleanup", "probe-rollback", "probe-release", "success"]) {
  const primary = new Error(canary), cleanup = new Error(canary), secondary = new Error(canary), records = [], statements = [], probeIds = [];
  let pools = 0;
  const observation = { onObservation(record) { records.push(record); throw new Error(canary); } };
  const createPool = (role, username) => {
    pools++;
    const allowed = { platform_schedule: role === "http" ? ["SELECT", "INSERT", "UPDATE"] : role === "dispatch" ? ["SELECT", "UPDATE"] : ["SELECT"],
      platform_outbox: role === "http" ? ["SELECT", "INSERT"] : role === "dispatch" ? ["SELECT", "INSERT", "UPDATE"] : ["SELECT"],
      test_entity: role === "http" ? ["SELECT", "INSERT", "UPDATE"] : role === "worker" ? ["SELECT", "DELETE"] : [],
      platform_processing: role === "worker" ? ["SELECT", "INSERT", "UPDATE"] : [], platform_record_change: [], platform_migration_history: [] };
    const query = async ({ text, values }) => {
      statements.push(text);
      if (text.startsWith("SELECT EXISTS")) {
        if (scenario === "body-and-pool-end") throw primary;
        return { rows: [{ exists: true, can_login: true, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false }] };
      }
      if (text.startsWith("WITH RECURSIVE memberships") || text.startsWith("SELECT has_database_privilege")) return { rows: [{ allowed: true }] };
      if (text.startsWith("SELECT current_user")) return { rows: [{ current_user: username, session_user: username, database: schedulingPolicy.database }] };
      if (text.startsWith("SELECT has_table_privilege")) return { rows: [{ allowed: allowed[values[0].split('"')[3]].includes(values[1]) }] };
      if (text === "ROLLBACK TO SAVEPOINT scheduling_permission_probe" && ["body-and-probe-cleanup", "probe-rollback"].includes(scenario)) throw cleanup;
      if (text === "RELEASE SAVEPOINT scheduling_permission_probe" && ["body-and-probe-cleanup", "probe-rollback", "probe-release"].includes(scenario)) throw scenario === "probe-release" ? cleanup : secondary;
      if (text.startsWith('SELECT * FROM "entity_smoke"."platform_schedule"') && scenario === "body-and-probe-cleanup") throw primary;
      const privilege = /^(SELECT|INSERT|UPDATE|DELETE|CREATE)\b/.exec(text)?.[1];
      const table = /"entity_smoke"\."?([a-z_]+)"?/.exec(text)?.[1];
      if (privilege && !allowed[table]?.includes(privilege)) throw Object.assign(new Error(canary), { code: "42501" });
      if (values?.length === 1 && ["INSERT", "UPDATE"].includes(privilege)) {
        assert.match(values[0], /^scheduler-permission-[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/);
        probeIds.push(values[0]);
      }
      return { rows: [] };
    };
    return { query, connect: async () => ({ query, release() {} }), end: async () => { if (scenario.endsWith("pool-end")) throw cleanup; } };
  };
  if (scenario === "success") {
    await proveSchedulingDatabaseAccess(schedulingPolicy, createPool, observation);
    assert.equal(pools, 3); assert.equal(probeIds.length, 3); assert.equal(new Set(probeIds).size, 2);
    assert.equal(records.length, 0);
    continue;
  }
  await assert.rejects(() => proveSchedulingDatabaseAccess(schedulingPolicy, createPool, observation), error => error === (scenario.startsWith("body-and-") ? primary : cleanup));
  assert.equal(pools, 1, "failure must stop before another authenticated identity is attempted");
  if (scenario.endsWith("pool-end")) assert(records.some(record => record.detail.phase === "pool-end"));
  else {
    assert.equal(statements.filter(text => text === "ROLLBACK TO SAVEPOINT scheduling_permission_probe").length, 1);
    assert.equal(statements.filter(text => text === "RELEASE SAVEPOINT scheduling_permission_probe").length, 1);
    assert(records.some(record => record.detail.phase === (scenario === "probe-release" ? "permission-code" : "rollback")));
    if (scenario === "body-and-probe-cleanup") assert(records.filter(record => record.detail.phase === "permission-code").length >= 2, "primary and companion failures retain separate observations");
  }
  assert(!JSON.stringify(records).includes(canary));
}
const partialQueries = [];
await assert.rejects(() => grantSchedulingDatabaseAccess(schedulingStateFixture({}, partialQueries, []).pool, schedulingPolicy));
assert(!partialQueries.some(text => /^(CREATE|ALTER|GRANT|REVOKE)/.test(text)), "Incomplete immutable history must reject before any role or privilege mutation.");
function schedulingStateFixture(inventory, statements, history = schedulingPolicy.manifest.migrations.map(({ id, checksum }) => ({ migration_id: id, checksum })), lockRows = [{ acquired: true }]) {
  let releases = 0;
  const query = async ({ text }) => {
    statements.push(text);
    if (text.startsWith("SELECT pg_try_advisory_xact_lock")) { if (lockRows instanceof Error) throw lockRows; return { rows: lockRows }; }
    if (text.startsWith("SELECT current_database()")) return { rows: [{ database: "entityfixture", owner: schedulingPolicy.migrationUsername }] };
    if (text.startsWith("SELECT pg_get_userbyid")) return { rows: [{ owner: schedulingPolicy.migrationUsername }] };
    if (text.startsWith("SELECT to_regclass")) return { rows: [{ relation: "entity_smoke.platform_migration_history" }] };
    if (text.startsWith("SELECT migration_id")) return { rows: history };
    if (text.startsWith("SELECT c.relname")) return { rows: ["platform_schedule", "platform_outbox", "platform_processing", "platform_record_change", "platform_migration_history", "test_entity"].map(name => ({ name, owner: schedulingPolicy.migrationUsername })) };
    if (text.startsWith("SELECT (SELECT COUNT(*) FROM information_schema")) return { rows: [{ allowed: true }] };
    if (text.startsWith("SELECT COUNT(*)::integer AS count FROM pg_proc")) return { rows: [{ count: 0 }] };
    if (text.startsWith("SELECT EXISTS (SELECT 1 FROM pg_class")) return { rows: [{ exists: true }] };
    if (text.includes("AS waiting_schedules")) { if (inventory instanceof Error) throw inventory; return { rows: inventory === undefined ? [] : [inventory] }; }
    return { rows: [] };
  };
  return { pool: { query, connect: async () => ({ query, release() { releases++; } }), end: async () => {} }, released: () => releases };
}
function fixture({ sessions = [], terminated = [], state, failAt, widened = false } = {}) {
  const statements = [];
  return { statements, pool: {
    async query(statement) {
      statements.push(statement);
      if (statement.text === failAt) throw Object.assign(new Error(canary), { code: "42501" });
      if (statement.text.startsWith("SELECT EXISTS")) {
        assert.deepEqual(statement.values, ["entity_smoke_runtime"]);
        return { rows: [{ exists: true, can_login: true, superuser: widened, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false }] };
      }
      if (statement.text.startsWith("SELECT pg_terminate_backend")) { assert.deepEqual(statement.values, ["entity_smoke_runtime"]); return { rows: terminated }; }
      if (statement.text.startsWith("SELECT 1 FROM pg_stat_activity")) { assert.deepEqual(statement.values, ["entity_smoke_runtime"]); return { rows: sessions }; }
      if (statement.text.startsWith("SELECT rolcanlogin")) { assert.deepEqual(statement.values, ["entity_smoke_runtime"]); return { rows: state ?? [{ can_login: false, iam_member: false }] }; }
      assert(["REVOKE rds_iam FROM entity_smoke_runtime", "ALTER ROLE entity_smoke_runtime NOLOGIN", "ALTER ROLE entity_smoke_runtime LOGIN", "GRANT rds_iam TO entity_smoke_runtime"].includes(statement.text));
      return { rows: [] };
    },
    connect: async () => { assert.fail("access controls must not imply transactional termination/rollback"); },
    end: async () => {},
  } };
}
for (const terminated of [[], [{ terminated: true }], [{ terminated: true }, { terminated: true }]]) {
  const test = fixture({ terminated });
  assert.equal(await performEntitySmokeAdministration(test.pool, "revoke-runtime", "entityfixture"), "ENTITY_SMOKE_ADMINISTRATION_CONFIRMED");
  assert.deepEqual(test.statements.slice(1).map(item => item.text.split(" FROM ")[0]), ["REVOKE rds_iam", "ALTER ROLE entity_smoke_runtime NOLOGIN", "SELECT pg_terminate_backend(pid) AS terminated", "SELECT 1", "SELECT rolcanlogin AS can_login, pg_has_role(rolname, 'rds_iam', 'member') AS iam_member"]);
}
const recovered = fixture({ state: [{ can_login: true, iam_member: true }] });
await performEntitySmokeAdministration(recovered.pool, "restore-runtime", "entityfixture");
assert(recovered.statements.findIndex(item => item.text.startsWith("SELECT 1")) < recovered.statements.findIndex(item => item.text.includes(" LOGIN")));
assert(!recovered.statements.some(item => /PASSWORD|ON .*test_entity|CREATE ROLE/.test(item.text)), "recovery cannot reset credentials, grants, data or identities");
for (const [operation, settings, field] of [
  ["revoke-runtime", { terminated: [{ terminated: false }] }, "sessions"],
  ["revoke-runtime", { terminated: [{ terminated: canary }] }, "sessions"],
  ["revoke-runtime", { sessions: [{}] }, "sessions"],
  ["revoke-runtime", { state: [{ can_login: true, iam_member: false }] }, "access-state"],
  ["revoke-runtime", { state: [] }, "access-state"],
  ["restore-runtime", { sessions: [{}] }, "sessions"],
  ["restore-runtime", { state: [{ can_login: true, iam_member: false }] }, "access-state"],
]) {
  const test = fixture(settings);
  await assert.rejects(() => performEntitySmokeAdministration(test.pool, operation, "entityfixture"), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation, field, condition: "not-confirmed", effect: "unknown" });
    const lines = [], previous = console.error;
    try { console.error = line => lines.push(JSON.parse(line)); reportEntitySmokeFailure("administration", "unknown", error); }
    finally { console.error = previous; }
    assert.deepEqual(lines[0].diagnostic, error.diagnosticRecord);
    assert(!JSON.stringify(lines).includes(canary));
    return true;
  });
  assert.equal(test.statements.filter(item => item.text === "ALTER ROLE entity_smoke_runtime LOGIN").length, operation === "restore-runtime" && field === "access-state" ? 1 : 0);
}
for (const operation of ["revoke-runtime", "restore-runtime"]) {
  const widened = fixture({ widened: true });
  await assert.rejects(() => performEntitySmokeAdministration(widened.pool, operation, "entityfixture"));
  assert.equal(widened.statements.length, 1, "a widened identity must fail before dependent changes");
}
for (const failAt of ["REVOKE rds_iam FROM entity_smoke_runtime", "ALTER ROLE entity_smoke_runtime NOLOGIN"]) {
  const test = fixture({ failAt });
  await assert.rejects(() => performEntitySmokeAdministration(test.pool, "revoke-runtime", "entityfixture"), error => error.message === canary);
  assert.equal(test.statements.filter(item => item.text === failAt).length, 1, "uncertain writes cannot be replayed");
  assert.equal(test.statements.at(-1).text, failAt, "a failure prevents later changes");
}
const invalid = fixture();
await assert.rejects(() => performEntitySmokeAdministration(invalid.pool, canary, "entityfixture"), error => error.diagnosticRecord.detail.field === "operation");
assert.equal(invalid.statements.length, 0);
const bootstrapStatements = []; let bootstrapReleased = false;
const bootstrapClient = { async query(statement) {
  bootstrapStatements.push(statement);
  if (statement.text.startsWith("SELECT has_database_privilege")) return { rows: [{ allowed: false }] };
  assert(["BEGIN", "SET LOCAL lock_timeout = '30000ms'", "SELECT pg_advisory_xact_lock(hashtext($1))", "ROLLBACK"].includes(statement.text), "missing database grant authority must prevent role or schema changes");
  return { rows: [] };
}, release: () => { bootstrapReleased = true; } };
await assert.rejects(() => performEntitySmokeAdministration({ connect: async () => bootstrapClient }, "bootstrap", "entityfixture"), error => {
  assert.deepEqual(error.diagnosticRecord.detail, { operation: "bootstrap", field: "privileges", condition: "not-confirmed", effect: "unknown" }); return true;
});
assert(bootstrapReleased);
assert.equal(bootstrapStatements.at(-1).text, "ROLLBACK");

// Model the actual RDS administrator, whose owner-selection authority does
// not require membership in the IAM-authenticated migration login.
const boundedFacts = { exists: true, can_login: true, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false };
const ownerGrant = 'GRANT entity_smoke_migration TO CURRENT_USER WITH INHERIT FALSE, SET TRUE';
function ownedFixture({ rejectHistory = false, rejectObservation = false, rejectRollback = false, authentication = [{ allowed: true }] } = {}) {
  const calls = []; let selected = false, released = false;
  const client = { async query(statement) {
    calls.push(statement);
    const text = statement.text;
    if (text.startsWith('GRANT entity_smoke_migration TO CURRENT_USER')) {
      assert.fail('bootstrap must never make the password administrator an IAM-role member');
    }
    if (text === 'SET LOCAL ROLE entity_smoke_migration') selected = true;
    if (text === 'ROLLBACK' && rejectRollback) throw new Error(canary);
    if (text.startsWith('SELECT EXISTS')) return { rows: [boundedFacts] };
    if (text.startsWith('SELECT has_database_privilege')) return { rows: [{ allowed: true }] };
    if (text.startsWith('SELECT pg_has_role')) return { rows: [{ member: true }] };
    if (text.startsWith('SELECT NOT EXISTS (WITH RECURSIVE memberships')) return { rows: authentication };
    if (text.startsWith('SELECT pg_get_userbyid')) return { rows: [{ owner: 'entity_smoke_migration' }] };
    if (text.startsWith('SELECT migration_id, checksum FROM')) {
      assert(selected, 'migration history cannot be read before selecting its noninherited owner');
      if (rejectHistory) throw Object.assign(new Error(canary), { code: '42501' });
      const { entitySmokeMigrationManifest } = require(join(root, 'infra/04.deploy/03.product/entrypoints/entity-smoke/postgresql.js'));
      return { rows: entitySmokeMigrationManifest().migrations.map(migration => ({ migration_id: migration.id, checksum: migration.checksum })) };
    }
    if (text.startsWith('SELECT has_schema_privilege')) {
      assert(selected, 'permission observation needs explicit owner-schema resolution');
      if (rejectObservation) throw Object.assign(new Error(canary), { code: '42501' });
      return { rows: [{ allowed: true }] };
    }
    return { rows: [] };
  }, release() { released = true; } };
  return { calls, released: () => released, pool: {
    connect: async () => client,
    query: async statement => {
      assert(statement.text.startsWith('SELECT EXISTS'), 'unselected pooled connections may only inspect bounded role facts');
      return { rows: [boundedFacts] };
    },
  } };
}
for (const operation of ['bootstrap', 'grant-runtime', 'observe-permissions']) {
  const test = ownedFixture();
  assert.equal(await performEntitySmokeAdministration(test.pool, operation, 'entityfixture'), 'ENTITY_SMOKE_ADMINISTRATION_CONFIRMED');
  assert(test.released());
  assert.equal(test.calls.at(-1).text, operation === 'observe-permissions' ? 'ROLLBACK' : 'COMMIT');
  if (operation === 'bootstrap') assert.equal(test.calls.filter(call => call.text === ownerGrant).length, 0);
  if (operation !== 'observe-permissions') assert.equal(test.calls.at(-2).text, `SELECT ${entitySmokePasswordAuthenticationPredicate} AS allowed`);
  if (operation === 'observe-permissions') {
    assert.equal(test.calls[0].text, 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');
    assert(test.calls.every(call => !/^(GRANT|REVOKE|ALTER|CREATE|INSERT|UPDATE|DELETE)\b/.test(call.text)), 'observation must remain read-only');
  }
}
for (const [operation, options] of [
  ['grant-runtime', { rejectHistory: true }],
  ['observe-permissions', { rejectObservation: true }],
  ['observe-permissions', { rejectRollback: true }],
]) {
  const test = ownedFixture(options);
  await assert.rejects(() => performEntitySmokeAdministration(test.pool, operation, 'entityfixture'), error => error.message === canary);
  assert(test.released());
  assert.equal(test.calls.at(-1).text, 'ROLLBACK');
  assert.equal(test.calls.filter(call => call.text === 'ROLLBACK').length, 1, 'rollback or failed operation cannot be retried');
  assert(!test.calls.some(call => call.text === 'COMMIT'));
  if (operation === 'grant-runtime') assert(!test.calls.some(call => call.text.startsWith('GRANT SELECT')), 'failed history verification must prevent runtime grants');
}
for (const operation of ['bootstrap', 'grant-runtime']) for (const authentication of [[], [{ allowed: false }], [{ allowed: canary }], [{ allowed: true }, { allowed: true }]]) {
  const test = ownedFixture({ authentication });
  await assert.rejects(() => performEntitySmokeAdministration(test.pool, operation, 'entityfixture'), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation, field: 'memberships', condition: 'not-confirmed', effect: 'unknown' }); return true;
  });
  assert.equal(test.calls.at(-1).text, 'ROLLBACK');
  assert(!test.calls.some(call => call.text === 'COMMIT'));
}
console.log("Entity-smoke access-control fixtures passed; controlled SQL responses, not effective PostgreSQL/RDS privilege proof.");
