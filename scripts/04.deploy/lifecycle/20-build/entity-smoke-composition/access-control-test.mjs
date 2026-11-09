// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.access-control
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
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
console.log("Entity-smoke access-control fixtures passed; controlled SQL responses, not effective PostgreSQL/RDS privilege proof.");
