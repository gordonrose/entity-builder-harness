// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.composition
//   version: 1
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove compiled public feature wiring, mapping, configuration and failure boundaries with controlled local dependencies.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.entity-smoke.composition.wrapper
//     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh

import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
const compiled = resolve(process.argv[2]);
const require = createRequire(join(compiled, "entity-smoke-probe.cjs"));
const imports = JSON.parse(readFileSync(join(compiled, "entity-smoke-payload.json"), "utf8")).required_imports;
for (const name of imports) assert(require.resolve(name).startsWith(join(compiled, "node_modules") + "/"), "every declared import must resolve in the actual compiled payload");
const app = require("@kanbien/app-entity-smoke");
assert.equal(typeof app.createEntitySmokePersistenceApp, "function");
for (const [entry, exported] of [["kanbien-entity-smoke.main", "runEntitySmokeMain"], ["kanbien-entity-smoke-migration.main", "runEntitySmokeMigration"],
  ["kanbien-entity-smoke-administration.main", "runEntitySmokeAdministration"], ["kanbien-entity-smoke-verifier.main", "runEntitySmokeVerifier"]]) {
  assert.equal(typeof require(join(compiled, entry + ".js"))[exported], "function");
}
const shared = require("@kanbien/core/shared");
const persistence = require("@kanbien/core/persistence");
const target = require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/postgresql.js"));
const config = require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/configuration.js"));
const { startPlatformServerProcess } = require("@kanbien/platform-server/main");
const certificate = readFileSync("platform/adapters/aws/persistence/postgresql/assets/rds-eu-west-1-bundle.crt", "utf8");
const canary = "synthetic-private-feature-canary";
const environment = { NODE_ENV: "test", PLATFORM_DEPLOYMENT_EXPOSURE: "private",
  PERSISTENCE_POSTGRES_HOST: "postgres", PERSISTENCE_POSTGRES_PORT: "5432", PERSISTENCE_POSTGRES_DATABASE: "entityfixture",
  PERSISTENCE_POSTGRES_SCHEMA: "entity_smoke", PERSISTENCE_RUNTIME_DATABASE_USERNAME: "entity_smoke_runtime",
  PERSISTENCE_MIGRATION_DATABASE_USERNAME: "entity_smoke_migration", PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1",
  PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-fixture/entity_smoke_runtime",
  PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/rds-eu-west-1-bundle.crt", ENTITY_SMOKE_LOCAL_QUALIFICATION_TOKEN: "entity-smoke-disposable-fixture" };
const valid = config.entitySmokeDatabaseSettings(environment, "runtime", () => certificate);
assert.equal(valid.ok, true); assert.equal(await valid.value.credentials.authenticationToken(), "entity-smoke-disposable-fixture");
for (const [key, value, code, detail] of [
  ["PERSISTENCE_POSTGRES_SCHEMA", "platform", "entity-smoke-target.configuration-invalid", { field: "schema", reason: "mismatch", effect: "not-started" }],
  ["PERSISTENCE_RUNTIME_DATABASE_USERNAME", "core_runtime", "entity-smoke-target.configuration-invalid", { field: "identity", reason: "mismatch", effect: "not-started" }],
  ["PLATFORM_DEPLOYMENT_EXPOSURE", "public", "entity-smoke-target.configuration-invalid", { field: "exposure", reason: "mismatch", effect: "not-started" }],
  ["PERSISTENCE_POSTGRES_HOST", undefined, "entity-smoke-target.database-configuration-invalid", { issues: [{ setting: "database.host", reason: "missing" }] }],
  ["PERSISTENCE_POSTGRES_PORT", canary, "entity-smoke-target.database-configuration-invalid", { issues: [{ setting: "database.port", reason: "invalid-integer" }] }],
]) {
  let reads = 0;
  const checked = config.entitySmokeDatabaseSettings({ ...environment, [key]: value }, "runtime", () => { reads++; return certificate; });
  assert.equal(checked.ok, false); assert.equal(reads, 0);
  assert.deepEqual(checked.error.diagnosticRecord, { schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  assert(!JSON.stringify(checked.error).includes(canary));
}
const failedRead = config.entitySmokeDatabaseSettings(environment, "runtime", () => { throw new Error(canary); });
assert.equal(failedRead.ok, false); assert.deepEqual(failedRead.error.diagnosticRecord.detail, { field: "authority", reason: "unavailable", effect: "not-started" });
assert(!JSON.stringify(failedRead.error).includes(canary));
const forbiddenToken = config.entitySmokeDatabaseSettings({ ...environment, NODE_ENV: "production" }, "runtime", () => certificate);
assert.equal(forbiddenToken.ok, false); assert.equal(forbiddenToken.error.diagnosticRecord.detail.field, "identity");
const manifest = target.entitySmokeMigrationManifest();
assert.equal(manifest.schema, "entity_smoke"); assert.equal(manifest.schemaPreprovisioned, true);
assert.equal(manifest.migrations.length, 1); assert.equal(manifest.migrations[0].id, "v0003_entity_smoke_test_entity");
assert(manifest.migrations[0].statements.every(statement => !statement.text.includes("__SCHEMA__") && statement.text.includes('"entity_smoke".test_entity')));
assert(manifest.migrations[0].statements[1].text.includes("test_entity_status_created_at_idx"));
assert.equal(manifest.migrations[0].checksum, createHash("sha256").update(manifest.migrations[0].statements.map(statement => statement.text).join("\n")).digest("hex"));

// The separate administrative observer reads one snapshot under the adapter's
// real migration lock. None of these injected results is database proof.
const administration = require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/administration.js"));
const targetDiagnostics = require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js"));
{
  const previousError = console.error, previousExit = process.exitCode;
  try {
    console.error = () => { throw new Error(canary); };
    assert.doesNotThrow(() => targetDiagnostics.reportEntitySmokeFailure("administration", "not-started", new Error(canary)));
    await administration.runEntitySmokeAdministration({ ENTITY_SMOKE_ADMINISTRATION_OPERATION: canary });
    assert.equal(process.exitCode, 1, "failed observation must not replace the failed operation's exit state or invoke dependent work");
  } finally { console.error = previousError; process.exitCode = previousExit; }
}
for (const [change, code, detail] of [
  [{ PERSISTENCE_IMPLEMENTATION: canary }, "kanbien-core-server.persistence-implementation-invalid", { phase: "implementation-selection", reason: "unsupported", effect: "not-started" }],
  [{ PERSISTENCE_POSTGRES_HOST: undefined }, "kanbien-core-server.configuration-invalid", { issues: [{ setting: "database.host", reason: "missing" }] }],
  [{}, "kanbien-core-server.administrator-credentials-invalid", { issues: [{ setting: "administrator.credentials", reason: "missing" }] }],
]) {
  const previousExit = process.exitCode, previousError = console.error, reports = [];
  try {
    console.error = line => reports.push(JSON.parse(line));
    await administration.runEntitySmokeAdministration({ ...environment, ENTITY_SMOKE_ADMINISTRATION_OPERATION: "bootstrap",
      PERSISTENCE_ADMINISTRATOR_SECRET_REFERENCE: "arn:aws:secretsmanager:eu-west-1:123456789012:secret:disposable-feature-fixture", ...change });
    assert.equal(process.exitCode, 1); assert.equal(reports.length, 1);
    assert.deepEqual(reports[0].diagnostic, { schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
    assert(!JSON.stringify(reports).includes(canary));
  } finally { process.exitCode = previousExit; console.error = previousError; }
}
function administrationFixture({ tables = { history: "history", entity: "entity", index: "index" }, history = [{ migration_id: manifest.migrations[0].id, checksum: manifest.migrations[0].checksum }], acquired = true, cause } = {}) {
  const statements = []; let releases = 0;
  const client = { query: async statement => {
    statements.push(statement);
    if (statement.text.includes("pg_try_advisory_xact_lock")) { assert.deepEqual(statement.values, ["kanbien-postgresql-migration:entity_smoke"]); return { rows: [{ acquired }], rowCount: 1 }; }
    if (statement.text.includes("to_regclass")) return { rows: [tables], rowCount: 1 };
    if (statement.text.startsWith("SELECT migration_id, checksum")) { if (cause) throw cause; return { rows: history, rowCount: history.length }; }
    assert(["BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY", "SET LOCAL statement_timeout = '30000ms'", "SET LOCAL ROLE entity_smoke_migration", "ROLLBACK"].includes(statement.text), "observer cannot write or invoke an undeclared query");
    return { rows: [], rowCount: 0 };
  }, release: () => { releases++; } };
  return { statements, releases: () => releases, pool: { connect: async () => client,
    query: async () => { throw new Error("observer must use its connected client"); }, end: async () => {} } };
}
for (const [settings, expected] of [
  [{ tables: { history: null, entity: null, index: null } }, "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED"],
  [{ tables: { history: "history", entity: null, index: null }, history: [] }, "PERSISTENCE_MIGRATION_STATE_REPLAY_PERMITTED"],
  [{}, "PERSISTENCE_MIGRATION_STATE_APPLIED_CONFIRMED"],
]) {
  const fixture = administrationFixture(settings);
  assert.equal(await administration.performEntitySmokeAdministration(fixture.pool, "observe-migration-state", "entityfixture"), expected);
  assert.equal(fixture.releases(), 1); assert.equal(fixture.statements.at(-1).text, "ROLLBACK");
}
for (const [settings, field, condition] of [
  [{ acquired: false }, "migration-lock", "already-running"],
  [{ acquired: "invalid" }, "migration-lock", "not-confirmed"],
  [{ tables: { history: null, entity: "orphan", index: null } }, "table-state", "mismatch"],
  [{ tables: { history: "history", entity: "orphan", index: null }, history: [] }, "table-state", "mismatch"],
  [{ history: [{ migration_id: "unreviewed", checksum: manifest.migrations[0].checksum }] }, "history-id", "mismatch"],
  [{ history: [{ migration_id: manifest.migrations[0].id, checksum: canary }] }, "history-checksum", "mismatch"],
  [{ history: [{}, {}] }, "history-count", "count-mismatch"],
  [{ tables: { history: "history", entity: null, index: "index" } }, "table-state", "missing"],
  [{ tables: { history: undefined, entity: null, index: null } }, "table-state", "not-confirmed"],
]) {
  const fixture = administrationFixture(settings);
  await assert.rejects(() => administration.performEntitySmokeAdministration(fixture.pool, "observe-migration-state", "entityfixture"), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation: "observe-migration-state", field, condition, effect: "not-assessed" });
    assert(!JSON.stringify(error).includes(canary));
    const lines = []; const previous = console.error;
    try { console.error = line => lines.push(JSON.parse(line)); targetDiagnostics.reportEntitySmokeFailure("administration", "unknown", error); }
    finally { console.error = previous; }
    assert.deepEqual(lines[0].diagnostic, error.diagnosticRecord, "the actual task reporter must retain the precise rejection");
    return true;
  });
  assert.equal(fixture.releases(), 1); assert.equal(fixture.statements.at(-1).text, "ROLLBACK");
}
const observerNative = Object.assign(new Error(canary), { code: "42501" });
const uncertainObserver = administrationFixture({ cause: observerNative });
await assert.rejects(() => administration.performEntitySmokeAdministration(uncertainObserver.pool, "observe-migration-state", "entityfixture"), error => error === observerNative);
assert.equal(uncertainObserver.releases(), 1);

const calls = [];
let providerError = Object.assign(new Error(canary), { code: "28P01" });
const failedPool = { query: async statement => { calls.push(statement); throw providerError; }, end: async () => {}, connect: async () => { throw new Error("unused"); } };
const failing = target.createEntitySmokePostgreSqlRuntime(failedPool);
const id = shared.entityId("a0b1c2d3-e4f5-4a67-8b90-123456789abc");
await assert.rejects(() => failing.repository.get(id), error => {
  assert.equal(error.code, "PLATFORM_PERSISTENCE_STORE_OPERATION_FAILED");
  assert.equal(error.diagnosticRecord.code, "persistence.credential-rejected");
  assert.deepEqual(error.diagnosticRecord.detail, { phase: "unknown", classification: "authentication_rejected", codeStatus: "recognized", operation: "read", boundary: "primary", effect: "not-assessed" });
  assert(!JSON.stringify(error).includes(canary)); return true;
});
assert.equal(calls.length, 1); assert(calls[0].text.includes('"entity_smoke".test_entity')); assert.deepEqual(calls[0].values, [id]);
const readiness = await failing.readiness(); assert.equal(readiness.readiness, "not-ready"); assert.equal(readiness.diagnosticRecord.code, "persistence.credential-rejected");
providerError = Object.assign(new Error(canary), { code: "ERR_TLS_CERT_ALTNAME_INVALID" });
let tlsFailure;
await assert.rejects(() => failing.repository.get(id), error => {
  tlsFailure = error;
  assert.equal(error.diagnosticRecord.code, "persistence.trust-validation-failed");
  assert(error.relatedDiagnosticRecords.some(record => record.code === "security.peer-identity-verification-failed"));
  assert(!JSON.stringify(error).includes(canary)); return true;
});

// Exercise the actual target startup consumer. Configuration, adapter/policy
// setup and app construction are real; pg transport, CA-file I/O and the server
// result are explicit protocols. This does not start a database or qualify an
// image; the separate mounted-HTTP cases below exercise the real server.
{
  const fs = require("node:fs"), pg = require("pg"), server = require("@kanbien/platform-server/main");
  const originalRead = fs.readFileSync, originalPool = pg.Pool, originalStart = server.startPlatformServerProcess;
  const previousError = console.error, previousExit = process.exitCode;
  const { runEntitySmokeMain } = require(join(compiled, "kanbien-entity-smoke.main.js"));
  let constructions = 0, closes = 0, starts = 0, closeFails = false, scenario, reports;
  const startupFailure = { code: "PLATFORM_SERVER_START_FAILED", defaultMessage: "Synthetic startup failure.", status: 500,
    diagnosticRecord: tlsFailure.diagnosticRecord, relatedDiagnosticRecords: tlsFailure.relatedDiagnosticRecords };
  const serverFailure = { ...startupFailure, diagnosticRecord: { schema: "core/diagnostic-record/v1",
    code: "platform-server.operation-failed", definitionVersion: 1,
    detail: { errorCode: "PLATFORM_SERVER_START_FAILED", phase: "listen", reason: "unclassified", effect: "unknown" } } };
  try {
    fs.readFileSync = (path, ...args) => path === environment.PERSISTENCE_POSTGRES_CA_PATH ? certificate : originalRead(path, ...args);
    pg.Pool = class {
      constructor(settings) {
        constructions++; assert.equal(settings.user, "entity_smoke_runtime");
        assert.equal(settings.ssl.rejectUnauthorized, true); assert.equal(settings.ssl.servername, "postgres");
      }
      on() {}
      query() { assert.fail("startup protocol must not execute business SQL"); }
      connect() { assert.fail("startup protocol must not connect to a real database"); }
      async end() { closes++; if (closeFails) throw new Error(canary); }
    };
    server.startPlatformServerProcess = async options => {
      starts++; assert.equal(options.apps.length, 2); assert.equal(options.env, environment);
      assert.deepEqual(options.diagnosticCatalogs, targetDiagnostics.entitySmokeServerDiagnosticCatalogs);
      if (scenario === "thrown") throw new Error(canary);
      if (scenario === "rejected") return { ok: false, error: startupFailure };
      if (scenario === "server-rejected") return { ok: false, error: serverFailure };
      return { ok: true, value: { close: async () => assert.fail("target must leave successful server ownership intact") } };
    };
    console.error = line => reports.push(JSON.parse(line));
    for (const selected of ["rejected", "server-rejected", "thrown", "success", "invalid-configuration"]) for (const failedClose of [false, true]) {
      scenario = selected; closeFails = failedClose; constructions = closes = starts = 0; reports = []; process.exitCode = undefined;
      await runEntitySmokeMain(selected === "invalid-configuration" ? { ...environment, PERSISTENCE_POSTGRES_SCHEMA: canary } : environment);
      assert.equal(constructions, selected === "invalid-configuration" ? 0 : 1, selected);
      assert.equal(starts, selected === "invalid-configuration" ? 0 : 1, selected);
      assert.equal(closes, ["rejected", "server-rejected", "thrown"].includes(selected) ? 1 : 0, "startup cleanup must be attempted once, never replayed after a close failure");
      assert.equal(process.exitCode, selected === "success" ? undefined : 1, selected);
      if (selected === "success") assert.deepEqual(reports, []);
      else {
        assert.equal(reports.length, ["rejected", "server-rejected", "thrown"].includes(selected) && failedClose ? 2 : 1, selected);
        if (["rejected", "server-rejected"].includes(selected)) {
          assert.deepEqual(reports[0].diagnostic, selected === "rejected" ? startupFailure.diagnosticRecord : serverFailure.diagnosticRecord);
          assert.deepEqual(reports[0].related_diagnostics, startupFailure.relatedDiagnosticRecords);
        } else if (selected === "thrown") {
          assert.equal(reports[0].diagnostic.code, "entity-smoke-target.boundary-failed");
          assert.deepEqual(reports[0].diagnostic.detail, { operation: "startup", effect: "unknown" });
        } else {
          assert.equal(reports[0].diagnostic.code, "entity-smoke-target.configuration-invalid");
          assert.deepEqual(reports[0].diagnostic.detail, { field: "schema", reason: "mismatch", effect: "not-started" });
        }
        if (["rejected", "server-rejected", "thrown"].includes(selected) && failedClose) {
          assert.equal(reports[1].diagnostic.code, "entity-smoke-target.boundary-failed");
          assert.deepEqual(reports[1].diagnostic.detail, { operation: "close", effect: "not-assessed" });
        }
        assert(reports.every(report => report.code === "ENTITY_SMOKE_OPERATION_NOT_CONFIRMED"));
        assert(!JSON.stringify(reports).includes(canary));
      }
    }
    reports = [];
    targetDiagnostics.reportEntitySmokeFailure("migration", "unknown", serverFailure);
    assert.equal(reports[0].diagnostic.code, "entity-smoke-target.boundary-failed");
    assert.deepEqual(reports[0].diagnostic.detail, { operation: "migration", effect: "unknown" },
      "startup-only Server selection must not widen SQL task diagnostics");
    assert(!targetDiagnostics.entitySmokeDiagnosticCatalogs.some(catalog => catalog.owner === "platform-server"));
  } finally {
    fs.readFileSync = originalRead; pg.Pool = originalPool; server.startPlatformServerProcess = originalStart;
    console.error = previousError; process.exitCode = previousExit;
  }
}

const reference = persistence.recordRetentionPolicyReference("entity-smoke.retention"); assert.equal(reference.ok, true);
const policy = persistence.recordLifecyclePolicy({ recoveryWindowMs: 60000, retentionPolicy: reference.value, legalHoldCheckRequired: true }); assert.equal(policy.ok, true);
let now = new Date("2026-11-07T12:00:00.000Z"), unavailable = false, failWrite = false, saves = 0, generated = 0;
const memory = app.inMemoryTestEntityRepository();
const providerFailure = tlsFailure;
const input = { integerValue: 7, uuidValue: "b0b1c2d3-e4f5-4a67-8b90-123456789abc", occurredAt: now.toISOString(),
  label: canary, status: "draft", enabled: false, categories: ["alpha"], notes: [canary], description: null, reviewedAt: null, secondaryCategories: null };
const syntheticEntity = { ...input, id, visibility: "active", lifecycle: { state: "active" }, createdAt: now.toISOString(), updatedAt: now.toISOString() };
const companion = tlsFailure.relatedDiagnosticRecords[0];
providerError = Object.assign(new Error(canary), { code: "23505", diagnosticRecord: tlsFailure.diagnosticRecord, relatedDiagnosticRecords: [companion] });
const beforeCollision = calls.length;
const collision = await failing.repository.create(syntheticEntity);
assert.equal(collision.ok, false); assert.equal(collision.error.code, "TEST_ENTITY_ID_CONFLICT");
assert.deepEqual(collision.error.diagnosticRecord, tlsFailure.diagnosticRecord, "creation conflicts retain a supplied primary diagnostic");
assert.deepEqual(collision.error.relatedDiagnosticRecords, [companion]);
assert.equal(calls.length, beforeCollision + 1, "a collision must not be retried");
assert(!JSON.stringify(collision).includes(canary));
const updateConflict = await failing.repository.save(syntheticEntity);
assert.equal(updateConflict.ok, false); assert.notEqual(updateConflict.error.code, "TEST_ENTITY_ID_CONFLICT", "an update conflict is not a generated-ID collision");
providerError = Object.assign(new Error(canary), { code: "23503" });
const constraintFailure = await failing.repository.create(syntheticEntity);
assert.equal(constraintFailure.ok, false); assert.notEqual(constraintFailure.error.code, "TEST_ENTITY_ID_CONFLICT", "other constraint failures cannot be labelled duplicate IDs");
const services = { repository: { get: key => memory.get(key), listByStatus: status => memory.listByStatus(status),
    create: entity => { saves++; return failWrite ? Promise.resolve({ ok: false, error: providerFailure }) : memory.create(entity); },
    save: entity => { saves++; return failWrite ? Promise.resolve({ ok: false, error: providerFailure }) : memory.save(entity); } },
  clock: { now: () => new Date(now) }, uuidGenerator: { generate: () => shared.uuid(generated++ === 0 ? id : "a0b1c2d3-e4f5-4a67-8b90-" + generated.toString(16).padStart(12, "0")) }, lifecyclePolicy: policy.value };
const logs = [];
const feature = app.createEntitySmokePersistenceApp({ services, readiness: async () => unavailable ? readiness : { readiness: "ready" }, close: async () => {} });
const started = await startPlatformServerProcess({ apps: [feature], host: "127.0.0.1", port: 0, installSignalHandlers: false,
  env: { NODE_ENV: "test", PLATFORM_DEPLOYMENT_EXPOSURE: "private" },
  diagnosticCatalogs: require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js")).entitySmokeServerDiagnosticCatalogs,
  logger: { write: record => logs.push(record) } });
assert.equal(started.ok, true, "actual public app mount must register successfully: " + JSON.stringify(started.ok ? {} : started.error));
const send = async command => { const response = await fetch("http://127.0.0.1:" + started.value.handle.port + "/entity-smoke/test-entity", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(command) }); return { status: response.status, body: await response.json() }; };
try {
  let result = await send({ action: "create", input: { ...input, enabled: canary } }); assert.equal(result.status, 400); assert.equal(saves, 0);
  result = await send({ action: "create", input }); assert.equal(result.status, 201); assert.equal(result.body.id, id); assert.equal(result.body.description, null);
  assert.deepEqual((await send({ action: "get", id })).body, result.body);
  assert.equal((await send({ action: "list", status: "draft" })).body.length, 1);
  assert.equal((await send({ action: "update", id, input: { status: "active", description: "", secondaryCategories: [], reviewedAt: now.toISOString() } })).status, 200);
  assert.equal((await send({ action: "list", status: "draft" })).body.length, 0);
  assert.equal((await send({ action: "list", status: "active" })).body.length, 1);
  assert.equal((await send({ action: "archive", id })).body.visibility, "archived");
  assert.equal((await send({ action: "restore-archive", id })).body.visibility, "active");
  assert.equal((await send({ action: "delete", id })).body.lifecycle.state, "deleted");
  assert.equal((await send({ action: "get", id })).status, 404);
  const deletedSaves = saves;
  assert.equal((await send({ action: "restore-archive", id })).status, 404);
  assert.equal((await send({ action: "update", id, input: { description: "must not change" } })).status, 404);
  assert.equal(saves, deletedSaves, "ordinary mutations cannot retrieve or write a deleted row");
  assert.equal((await send({ action: "list", status: "active" })).body.length, 0);
  assert.equal((await send({ action: "restore-deleted", id })).body.lifecycle.state, "active");
  await send({ action: "delete", id }); now = new Date(now.getTime() + 60001);
  result = await send({ action: "restore-deleted", id }); assert.equal(result.status, 400); assert.equal(result.body.error.code, "PERSISTENCE_RESTORE_WINDOW_EXPIRED");
  assert.equal((await memory.get(id)).lifecycle.state, "deleted");
  for (const [retentionSatisfied, legalHold, expected] of [[false, false, "retention-not-met"], [true, true, "legal-hold"], [true, false, "eligible"]]) {
    assert.equal((await send({ action: "assess-purge", id, retentionSatisfied, legalHold })).body.eligibility, expected);
  }
  assert.equal((await send({ action: "purge", id })).status, 400);
  const before = saves; failWrite = true;
  result = await send({ action: "create", input }); assert.equal(result.status, 503); assert.equal(saves, before + 1);
  unavailable = true;
  const ready = await fetch("http://127.0.0.1:" + started.value.handle.port + "/readyz"); assert.notEqual(ready.status, 200);
  const live = await fetch("http://127.0.0.1:" + started.value.handle.port + "/livez"); assert.equal(live.status, 200);
  const delivered = logs.filter(record => record.message === "platform.diagnostic.observed").map(record => record.fields.diagnostic);
  assert(delivered.some(record => record.code === "security.peer-identity-verification-failed"));
  assert(!JSON.stringify(logs).includes(canary));
} finally { await started.value.close(); }
let captured;
feature.mount({ registerDiagnosticCatalog: () => shared.ok(undefined), registerObservabilityProfile: () => shared.ok(undefined),
  registerHealthCheck: () => shared.ok(undefined), registerRoute: route => { captured = route.handler; return shared.ok(undefined); } });
const beforeObserverFailure = saves;
const observedFailure = await captured.handle({ body: { action: "create", input } }, { onDiagnostic: () => { throw new Error(canary); } });
assert.equal(observedFailure.status, 503); assert.equal(saves, beforeObserverFailure + 1);
assert.equal(observedFailure.observability.diagnosticRecord, providerFailure.diagnosticRecord);
// The same deployed verifier consumes real HTTP here. Only release metadata
// and the timer are controlled; this is not image/source-custody evidence.
failWrite = false; unavailable = false;
const { verifyEntitySmokeFeature } = require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/verification.js"));
const proofServer = await startPlatformServerProcess({ apps: [feature], host: "127.0.0.1", port: 0, installSignalHandlers: false,
  env: { NODE_ENV: "test", PLATFORM_DEPLOYMENT_EXPOSURE: "private" },
  diagnosticCatalogs: require(join(compiled, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js")).entitySmokeServerDiagnosticCatalogs,
  logger: { write: record => logs.push(record) } });
assert.equal(proofServer.ok, true);
assert.notEqual(proofServer.value.handle.port, started.value.handle.port, "separate listeners must not reuse the first fixture's pooled connection");
const proofOptions = { localFixture: true, expectedSource: "local-uncommitted", baseUrl: "http://127.0.0.1:" + proofServer.value.handle.port + "/",
  label: "entity-smoke-" + "a".repeat(24), clock: services.clock,
  sleep: async milliseconds => { assert.equal(milliseconds, 60050); now = new Date(now.getTime() + milliseconds); },
  request: async (url, options) => {
    assert.equal(options.redirect, "error");
    if (new URL(url).pathname === "/internal/release-verification") return new Response(JSON.stringify({ release: { sourceCommitSha: "local-uncommitted" } }), { status: 200 });
    try { return await fetch(url, options); }
    catch (error) {
      const code = ["ECONNREFUSED", "UND_ERR_SOCKET", "UND_ERR_INVALID_ARG", "ERR_INVALID_URL"].includes(error?.cause?.code) ? error.cause.code : "unclassified";
      const observations = logs.slice(-15).flatMap(record => record.fields?.diagnostic ? [record.fields.diagnostic] : []);
      console.error(JSON.stringify({ fixture: "private-proof-request", deadline_aborted: Boolean(options.signal?.aborted), code, observations })); throw error;
    }
  } };
try {
  const createdProof = await verifyEntitySmokeFeature({ ...proofOptions, operation: "create" });
  assert.equal(createdProof.code, "ENTITY_SMOKE_RECORD_CREATED"); assert.match(createdProof.record_digest, /^[a-f0-9]{64}$/);
  const readProof = await verifyEntitySmokeFeature({ ...proofOptions, operation: "read", expectedDigest: createdProof.record_digest });
  assert.equal(readProof.code, "ENTITY_SMOKE_RECORD_RETRIEVED"); assert.equal(readProof.record_digest, createdProof.record_digest);
  const beforeMissing = saves;
  const reconciledProof = await verifyEntitySmokeFeature({ ...proofOptions, operation: "observe-create" });
  assert.equal(reconciledProof.code, "ENTITY_SMOKE_RECORD_RECONCILED");
  assert.equal(reconciledProof.record_digest, createdProof.record_digest);
  assert.equal(saves, beforeMissing, "lost-create reconciliation observes the original; it never recreates");
  await assert.rejects(() => verifyEntitySmokeFeature({ ...proofOptions, operation: "observe-create", label: "entity-smoke-" + "c".repeat(24) }), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation: "observe-create", step: "list", condition: "missing-record", effect: "not-assessed" }); return true;
  });
  await assert.rejects(() => verifyEntitySmokeFeature({ ...proofOptions, operation: "read", label: "entity-smoke-" + "c".repeat(24), expectedDigest: createdProof.record_digest }), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation: "read", step: "list", condition: "missing-record", effect: "not-assessed" }); return true;
  });
  await assert.rejects(() => verifyEntitySmokeFeature({ ...proofOptions, operation: "read", expectedDigest: "0".repeat(64) }), error => {
    assert.equal(error.diagnosticRecord.detail.condition, "digest-mismatch"); return true;
  });
  assert.equal(saves, beforeMissing, "read proofs never recreate missing or mismatched facts");
  const lifecycle = await verifyEntitySmokeFeature({ ...proofOptions, operation: "lifecycle", label: "entity-smoke-" + "b".repeat(24) });
  assert.equal(lifecycle.code, "ENTITY_SMOKE_LIFECYCLE_PROVEN");
  assert.deepEqual(lifecycle.steps, ["release", "liveness", "readiness", "create", "read", "update", "list", "archive", "restore-archive", "delete", "restore-deleted", "purge-eligibility"]);
  assert.equal((await verifyEntitySmokeFeature({ ...proofOptions, operation: "read", expectedDigest: createdProof.record_digest })).record_digest, createdProof.record_digest);
  let requests = 0;
  await assert.rejects(() => verifyEntitySmokeFeature({ ...proofOptions, operation: "create", baseUrl: "https://example.invalid/", request: async () => { requests++; throw new Error(canary); } }), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation: "create", step: "configuration", condition: "invalid-input", effect: "not-started" });
    assert(!JSON.stringify(error).includes(canary)); return true;
  });
  assert.equal(requests, 0, "an undeclared/internet endpoint is rejected before requests");
  const beforeCleanup = saves;
  const cleaned = await verifyEntitySmokeFeature({ ...proofOptions, operation: "cleanup", expectedDigest: createdProof.record_digest });
  assert.equal(cleaned.code, "ENTITY_SMOKE_SYNTHETIC_RECORD_LOGICALLY_DELETED");
  assert.equal(cleaned.record_digest, createdProof.record_digest);
  assert.deepEqual(cleaned.steps, ["release", "liveness", "readiness", "read", "delete"]);
  assert.equal(saves, beforeCleanup + 1, "cleanup is one server-mediated logical deletion, not a purge or replay");
} finally { await proofServer.value.close(); }
console.log("Entity-smoke compiled public app, target configuration, mapping and HTTP lifecycle proof passed (controlled local dependencies; no database/AWS claim).");

