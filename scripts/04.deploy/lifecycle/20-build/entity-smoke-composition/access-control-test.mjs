// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.access-control
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-11"
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
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
const require = createRequire(import.meta.url);
const root = resolve(process.argv[2]);
const { performEntitySmokeAdministration } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/administration.js"));
const { entitySmokePasswordAuthenticationPredicate } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/preflight.js"));
const { reportEntitySmokeFailure } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js"));
const canary = "private-session-and-credential-canary";
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
    if (text.startsWith('SELECT checksum FROM')) {
      assert(selected, 'migration history cannot be read before selecting its noninherited owner');
      if (rejectHistory) throw Object.assign(new Error(canary), { code: '42501' });
      const { entitySmokeMigrationManifest } = require(join(root, 'infra/04.deploy/03.product/entrypoints/entity-smoke/postgresql.js'));
      return { rows: [{ checksum: entitySmokeMigrationManifest().migrations[0].checksum }] };
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
