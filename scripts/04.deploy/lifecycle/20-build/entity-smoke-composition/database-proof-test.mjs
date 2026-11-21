// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.database-proof
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Reject ineffective SQL denials and restore recreation or changed original facts through actual compiled proof consumers.
//   portability: {class: internal, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.test.entity-smoke.composition.wrapper
//     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { join, resolve } from "node:path";
const require = createRequire(import.meta.url), root = resolve(process.argv[2]);
const { verifyEntitySmokeDatabase } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/database-verification.js"));
const { entitySmokeRecordDigest } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/proof-facts.js"));
const { reportEntitySmokeFailure } = require(join(root, "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js"));
const label = "entity-smoke-" + "a".repeat(24), canary = "credential-row-provider-canary";
function fixture({ allowed, deniedCode = "42501", rollbackFails = false, widened = false, rows = [], getRows = rows, collisionCode = "23505", allowCreate = false } = {}) {
  const statements = []; let releases = 0;
  const client = { async query(statement) {
    statements.push(statement);
    if (statement.text === "ROLLBACK" && rollbackFails) throw new Error(canary);
    if (/^(BEGIN|SET LOCAL|ROLLBACK|SAVEPOINT)/.test(statement.text)) return { rows: [] };
    if (statement.text.startsWith("INSERT")) {
      if (allowCreate) return { rows, rowCount: 1 };
      throw Object.assign(new Error(canary), { code: collisionCode });
    }
    if (statement.text.startsWith("SELECT ")) { statements.pop(); return pool.query(statement); }
    if (statement.text === allowed) return { rows: [] };
    throw Object.assign(new Error(canary), { code: deniedCode });
  }, release: () => { releases++; } };
  const pool = { async query(statement) {
    statements.push(statement);
    if (statement.text.startsWith("SELECT current_user")) return { rows: [{ username: "entity_smoke_runtime", superuser: widened, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false }] };
    assert(statement.text.startsWith("SELECT "), "restore verification may not change data or recreate a missing record");
    if (statement.text.includes("WHERE id =")) { assert.deepEqual(statement.values, [rows[0].id]); return { rows: getRows, rowCount: getRows.length }; }
    assert.deepEqual(statement.values, ["draft"]);
    return { rows, rowCount: rows.length };
  }, connect: async () => client, end: async () => {} };
  return { pool, statements, releases: () => releases };
}
const passed = fixture();
const result = await verifyEntitySmokeDatabase(passed.pool, { operation: "permissions", label });
assert.deepEqual(result.steps, ["identity", "delete", "truncate", "create-table", "alter-table", "drop-table", "history-write"]);
assert.equal(passed.releases(), 1);
assert.equal(passed.statements.filter(item => item.text === "ROLLBACK").length, 6);
const probes = passed.statements.filter(item => !/^(BEGIN|SET LOCAL|ROLLBACK|SELECT current_user)/.test(item.text));
assert.equal(probes.length, 6);
async function rejected(settings, options, step, condition, effect = "not-assessed") {
  const test = fixture(settings);
  await assert.rejects(() => verifyEntitySmokeDatabase(test.pool, { operation: "permissions", label, ...options }), error => {
    assert.deepEqual(error.diagnosticRecord.detail, { operation: options?.operation ?? "permissions", step, condition, effect });
    const output = [], original = console.error;
    try { console.error = line => output.push(JSON.parse(line)); reportEntitySmokeFailure("verification", "unknown", error); }
    finally { console.error = original; }
    assert.deepEqual(output[0].diagnostic, error.diagnosticRecord);
    if (settings.deniedCode === "28P01") {
      assert(output[0].related_diagnostics.some(record => record.code === "persistence.credential-rejected"), "unexpected database failures retain the classified provider observation");
    }
    assert(!JSON.stringify(output).includes(canary));
    return true;
  });
  return test;
}
for (const probe of probes) {
  const test = await rejected({ allowed: probe.text }, {}, result.steps[probes.indexOf(probe) + 1], "unexpectedly-allowed");
  assert.equal(test.statements.at(-1).text, "ROLLBACK");
  assert.equal(test.statements.filter(item => item.text === probe.text).length, 1);
}
await rejected({ deniedCode: "28P01" }, {}, "delete", "unexpected-failure");
await rejected({ rollbackFails: true }, {}, "rollback", "unexpected-failure", "unknown");
const elevated = await rejected({ widened: true }, {}, "identity", "not-confirmed");
assert.equal(elevated.statements.length, 1);
const invalid = await rejected({}, { operation: "restore-read", expectedDigest: canary }, "configuration", "invalid-input", "not-started");
assert.equal(invalid.statements.length, 0);
const record = { id: "a0b1c2d3-e4f5-4a67-8b90-123456789abc", integerValue: 7,
  uuidValue: "b0b1c2d3-e4f5-4a67-8b90-123456789abc", occurredAt: "2026-11-07T12:00:00.000Z", label,
  status: "draft", enabled: false, categories: ["alpha", "gamma"], notes: ["first", ""], description: null, reviewedAt: null,
  secondaryCategories: null, visibility: "active", lifecycle: { state: "active" }, createdAt: "2026-11-08T12:00:00.000Z", updatedAt: "2026-11-08T12:00:00.000Z" };
const row = Object.fromEntries(Object.entries(record).map(([key, value]) => [key.replace(/[A-Z]/g, letter => "_" + letter.toLowerCase()), value]));
const expectedDigest = entitySmokeRecordDigest(record);
const restored = fixture({ rows: [row] });
const restoredResult = await verifyEntitySmokeDatabase(restored.pool, { operation: "restore-read", label, expectedDigest });
assert.equal(restoredResult.record_digest, expectedDigest);
assert.equal(restoredResult.code, "ENTITY_SMOKE_RESTORED_RECORD_RETRIEVED");
assert(!JSON.stringify(restoredResult).includes(record.id));
assert.equal(restored.releases(), 1);
assert(restored.statements.some(item => item.text === "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY"));
assert(!restored.statements.some(item => /^(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|ALTER|DROP)/.test(item.text)), "restore read must never run structural probes");
await rejected({}, { operation: "restore-read", expectedDigest }, "read", "missing-record");
await rejected({ rows: [row, row] }, { operation: "restore-read", expectedDigest }, "read", "multiple-records");
await rejected({ rows: [row], getRows: [] }, { operation: "restore-read", expectedDigest }, "read", "missing-record");
for (const changed of [{ integer_value: 8 }, { id: "c0b1c2d3-e4f5-4a67-8b90-123456789abc" }, { created_at: "2026-11-08T12:00:01.000Z" }, { secondary_categories: [] }]) {
  await rejected({ rows: [{ ...row, ...changed }] }, { operation: "restore-read", expectedDigest }, "read", "digest-mismatch");
}
const collision = fixture({ rows: [row] });
const collisionResult = await verifyEntitySmokeDatabase(collision.pool, { operation: "collision", label, expectedDigest });
assert.equal(collisionResult.code, "ENTITY_SMOKE_IDENTIFIER_COLLISION_PROVEN");
assert.deepEqual(collisionResult.steps, ["identity", "read", "collision", "read"]);
assert.equal(collision.statements.filter(item => item.text.startsWith("INSERT")).length, 1);
assert(collision.statements.some(item => item.text === "ROLLBACK TO SAVEPOINT entity_smoke_duplicate_probe"));
assert.equal(collision.statements.at(-1).text, "ROLLBACK");
await rejected({ rows: [row], allowCreate: true }, { operation: "collision", expectedDigest }, "collision", "unexpectedly-allowed");
const unrelated = fixture({ rows: [row], collisionCode: "23503" });
await assert.rejects(() => verifyEntitySmokeDatabase(unrelated.pool, { operation: "collision", label, expectedDigest }), error => error.code !== "TEST_ENTITY_ID_CONFLICT");
assert.equal(unrelated.statements.at(-1).text, "ROLLBACK");
console.log("Entity-smoke database proof fixtures passed; controlled provider responses, not real PostgreSQL or isolated RDS restoration.");
