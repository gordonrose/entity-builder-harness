// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.preflight
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Exercise actual packaged-mode callers and read-only preflight SQL, safe rejection and cleanup with controlled database responses.
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
const { performEntitySmokeDatabasePreflight: preflight } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/preflight.js"));
const { reportEntitySmokeFailure } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js"));
const canary = "private-preflight-user-and-provider-canary";
const identities = { administration: "core_administrator", migration: "entity_smoke_migration", runtime: "entity_smoke_runtime" };
function fixture(identity, changes = {}) {
  const statements = []; let releases = 0, ends = 0;
  const client = { async query(statement) {
    statements.push(statement);
    if (statement.text === "ROLLBACK" && changes.rollback) throw new Error(canary);
    if (statement.text.startsWith("SELECT current_user")) {
      if (changes.body) throw changes.body;
      return { rows: changes.connection ?? [{ username: identities[identity], database: "entityfixture" }] };
    }
    if (statement.text.startsWith("SELECT EXISTS")) return { rows: [{ exists: true, can_login: true, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false }] };
    if (statement.text.startsWith("SELECT has_database_privilege") || statement.text.startsWith("SELECT pg_has_role")) return { rows: changes.authority ?? [{ allowed: true }] };
    if (statement.text.startsWith("SELECT pg_get_userbyid") || statement.text.startsWith("SELECT has_schema_privilege")) return { rows: changes.schema ?? [{ allowed: true }] };
    assert(["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY", "SET LOCAL statement_timeout = '5000ms'", "ROLLBACK"].includes(statement.text), "preflight cannot perform a write, SET ROLE, bootstrap, migration or denial probe");
    return { rows: [] };
  }, release() { releases++; if (changes.release) throw new Error(canary); } };
  return { statements, releases: () => releases, ends: () => ends,
    pool: { query: async () => assert.fail("preflight must use the same connected transaction"), connect: async () => client, end: async () => { ends++; if (changes.end) throw new Error(canary); } } };
}
const options = identity => ({ identity, database: "entityfixture", username: identities[identity] });
for (const identity of Object.keys(identities)) {
  const test = fixture(identity);
  assert.equal(await preflight(test.pool, options(identity)), "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED");
  assert.equal(test.releases(), 1);
  assert.equal(test.statements.at(-1).text, "ROLLBACK");
  assert(!test.statements.some(s => /^(?:INSERT|UPDATE|DELETE|CREATE|ALTER|GRANT|REVOKE|COMMIT|TRUNCATE|DROP)\b/.test(s.text)));
}
for (const [changes, field, condition] of [
  [{ connection: [] }, "identity", "count-mismatch"],
  [{ connection: [{ username: null, database: "entityfixture" }] }, "identity", "wrong-type"],
  [{ connection: [{ username: canary, database: "entityfixture" }] }, "identity", "mismatch"],
  [{ connection: [{ username: identities.administration, database: false }] }, "database", "wrong-type"],
  [{ connection: [{ username: identities.administration, database: canary }] }, "database", "mismatch"],
  [{ authority: [] }, "authority", "count-mismatch"],
  [{ authority: [{ allowed: canary }] }, "authority", "wrong-type"],
  [{ authority: [{ allowed: false }] }, "authority", "not-confirmed"],
  [{ rollback: true }, "rollback", "not-confirmed"],
]) {
  const test = fixture("administration", changes);
  await assert.rejects(() => preflight(test.pool, options("administration")), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { identity: "administration", field, condition, effect: "not-started" });
    const reports = [], old = console.error;
    try { console.error = line => reports.push(JSON.parse(line)); reportEntitySmokeFailure("administration", "not-started", error); }
    finally { console.error = old; }
    assert.deepEqual(reports[0].diagnostic, error.diagnosticRecord);
    assert(!JSON.stringify(reports).includes(canary)); return true;
  });
  assert.equal(test.releases(), 1); assert.equal(test.statements.at(-1).text, "ROLLBACK");
  if (field === "identity" || field === "database") assert.equal(test.statements.length, 4, "failed identity must prevent privilege reads");
}
for (const identity of ["migration", "runtime"]) for (const [rows, condition] of [[[], "count-mismatch"], [[{ allowed: null }], "wrong-type"], [[{ allowed: false }], "not-confirmed"]]) {
  const test = fixture(identity, { schema: rows });
  await assert.rejects(() => preflight(test.pool, options(identity)), error => error.diagnosticRecord.detail.field === "schema" && error.diagnosticRecord.detail.condition === condition);
}
const native = new Error(canary), failed = fixture("administration", { body: native, rollback: true });
const oldError = console.error, rollbackReports = [];
try { console.error = line => rollbackReports.push(JSON.parse(line)); await assert.rejects(() => preflight(failed.pool, options("administration")), error => error === native); }
finally { console.error = oldError; }
assert.equal(failed.releases(), 1); assert.equal(rollbackReports[0].diagnostic.detail.field, "rollback");
assert(!JSON.stringify(rollbackReports).includes(canary));
const releaseFailed = fixture("administration", { release: true });
await assert.rejects(() => preflight(releaseFailed.pool, options("administration")), error => error.message === canary);
const releaseAfterBody = fixture("administration", { body: native, release: true });
try { console.error = line => rollbackReports.push(JSON.parse(line)); await assert.rejects(() => preflight(releaseAfterBody.pool, options("administration")), error => error === native); }
finally { console.error = oldError; }
assert.equal(rollbackReports.at(-1).diagnostic.detail.operation, "close");
const invalid = fixture("runtime");
await assert.rejects(() => preflight(invalid.pool, { ...options("runtime"), username: identities.administration }), error => error.diagnosticRecord.detail.field === "configuration");
assert.equal(invalid.statements.length, 0);

// Exercise the real three entrypoint callers and real configuration/adapter
// constructors. Only pg transport and the checked CA-file read are doubled.
const fs = require("node:fs"), pg = require("pg");
const certificate = fs.readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const originalRead = fs.readFileSync, originalPool = pg.Pool, oldLog = console.log, oldExit = process.exitCode;
let selected;
const base = { NODE_ENV: "test", PLATFORM_DEPLOYMENT_EXPOSURE: "private", PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432",
  PERSISTENCE_POSTGRES_DATABASE: "entityfixture", PERSISTENCE_POSTGRES_SCHEMA: "entity_smoke", PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/rds-eu-west-1-bundle.crt",
  PERSISTENCE_RUNTIME_DATABASE_USERNAME: "entity_smoke_runtime", PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration",
  PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1", ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN: "entity-smoke-disposable-fixture" };
try {
  fs.readFileSync = (path, ...args) => path === base.PERSISTENCE_POSTGRES_CA_PATH ? certificate : originalRead(path, ...args);
  pg.Pool = class {
    constructor(settings) { assert.equal(settings.user, identities[selected.identity]); assert.equal(settings.ssl.rejectUnauthorized, true); assert.equal(settings.ssl.servername, "postgres"); }
    on() {}
    async connect() { const client = await selected.test.pool.connect(); return { query: (text, values) => client.query({ text, values }), release: () => client.release() }; }
    end() { return selected.test.pool.end(); }
    query() { assert.fail("preflight must not use an unbound pool query"); }
  };
  for (const identity of Object.keys(identities)) for (const scenario of ["success", "semantic", "denied", "denied-release", "rollback", "release", "end"]) {
    const reports = [], failures = [];
    const changes = scenario === "semantic" ? { connection: [{ username: canary, database: "entityfixture" }] }
      : scenario.startsWith("denied") ? { body: Object.assign(new Error(canary), { code: "42501" }), release: scenario === "denied-release" }
      : scenario === "rollback" ? { rollback: true } : scenario === "release" ? { release: true } : scenario === "end" ? { end: true } : {};
    selected = { identity, test: fixture(identity, changes) }; process.exitCode = undefined;
    console.log = line => reports.push(JSON.parse(line)); console.error = line => failures.push(JSON.parse(line));
    if (identity === "administration") {
      const { runEntitySmokeAdministration } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/administration.js"));
      await runEntitySmokeAdministration({ ...base, ENTITY_SMOKE_ADMINISTRATION_OPERATION: "preflight",
        PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:fixture-admin",
        PERSISTENCE_ADMINISTRATOR_CREDENTIALS: JSON.stringify({ username: identities[identity], password: canary }) });
    } else if (identity === "migration") {
      const { runEntitySmokeMigration } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/migrations.js"));
      await runEntitySmokeMigration({ ...base, ENTITY_SMOKE_MIGRATION_OPERATION: "preflight", PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-fixture/" + identities[identity] });
    } else {
      const { runEntitySmokeDatabaseProof } = require(join(root, "infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke-database-proof.main.js"));
      await runEntitySmokeDatabaseProof({ ...base, ENTITY_SMOKE_DATABASE_PROOF_OPERATION: "preflight", ENTITY_SMOKE_PROOF_LABEL: "entity-smoke-" + "e".repeat(24), PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-fixture/" + identities[identity] });
    }
    if (scenario === "success") {
      assert.deepEqual(failures, []); assert.equal(process.exitCode, undefined); assert.equal(reports.length, 1);
      assert.equal(reports[0].code, "ENTITY_SMOKE_DATABASE_PREFLIGHT_CONFIRMED");
    } else {
      assert.equal(process.exitCode, 1); assert.equal(reports.length, 0); assert.equal(failures.length, scenario === "denied-release" ? 2 : 1);
      if (scenario === "semantic" || scenario === "rollback") {
        assert.equal(failures[0].diagnostic.code, "entity-smoke-target.preflight-rejected");
        assert.equal(failures[0].diagnostic.detail.identity, identity);
        assert.equal(failures[0].diagnostic.detail.field, scenario === "semantic" ? "identity" : "rollback");
      }
      if (scenario.startsWith("denied")) {
        assert.equal(failures.at(-1).diagnostic.code, "persistence.runtime-permission-denied");
        assert.deepEqual(failures.at(-1).diagnostic.detail, { phase: "query", classification: "permission_denied", codeStatus: "recognized", operation: "readiness", effect: "not-assessed" });
        if (scenario === "denied-release") assert.equal(failures[0].diagnostic.detail.operation, "close");
      }
      if (scenario === "end") assert.equal(failures[0].diagnostic.detail.operation, "close");
      assert(!JSON.stringify(failures).includes(canary));
      assert.equal(selected.test.statements.filter(s => s.text.startsWith("SELECT current_user")).length, 1, "failed queries are never retried");
    }
    assert.equal(selected.test.releases(), 1); assert.equal(selected.test.ends(), 1);
    assert(!JSON.stringify(reports).includes(canary));
  }
} finally { fs.readFileSync = originalRead; pg.Pool = originalPool; console.log = oldLog; console.error = oldError; process.exitCode = oldExit; }
console.log("Entity-smoke preflight callers passed with controlled pg transport; no live database or IAM claim.");
