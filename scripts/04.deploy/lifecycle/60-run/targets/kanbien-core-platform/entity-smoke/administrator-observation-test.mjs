// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.administrator-observation
//   version: 1
//   status: draft
//   created_on: "2026-11-11"
//   updated_on: "2026-11-11"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Exercise fixed read-only catalogue observation and safe failed-phase reports using controlled clients.
//   portability: {class: internal, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.library.entity-smoke.administrator-observation
//     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-observation.js

// Controlled caller proof, not PostgreSQL/RDS access evidence.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('./administrator-observation.js', import.meta.url), 'utf8');
async function run(failAt) {
  const calls = [], output = []; let closed = 0;
  const client = { async connect() { if (failAt === 'connection') throw Error('sensitive-canary'); }, async end() { closed++; }, async query(q) {
    const sql = typeof q === 'string' ? q : q.text; calls.push(sql);
    assert(/^(SELECT|BEGIN READ ONLY|ROLLBACK)/.test(sql));
    if (failAt === 'observation') throw Error('sensitive-canary');
    if (sql.startsWith('SELECT current_user')) return { rows: [{ allowed: true }] };
    if (sql.startsWith('SELECT r.rolname')) return { rows: [{ role: 'entity_smoke_migration', member: 'core_migration', grantor: 'sensitive-canary', admin_option: false, inherit_option: false, set_option: true }] };
    if (sql.startsWith('SELECT pg_has_role')) return { rows: [{ member: true, usage: false, selectable: true }] };
    return { rows: [] };
  } };
  const process = { env: { PERSISTENCE_POSTGRES_HOST: failAt === 'configuration' ? 'sensitive-canary' : 'kanbien-core-platform-persistence.cl62wkc0w898.eu-west-1.rds.amazonaws.com', PERSISTENCE_POSTGRES_DATABASE: 'kanbienpersistence', PERSISTENCE_MIGRATION_DATABASE_USERNAME: 'entity_smoke_migration' } };
  vm.runInNewContext(source, { process, console: { log: s => output.push(JSON.parse(s)), error: s => output.push(JSON.parse(s)) }, require(name) {
    if (name.endsWith('/pg')) return { Client: function(options) { assert.equal(options.ssl.rejectUnauthorized, true); assert.equal(options.user, 'entity_smoke_migration'); return client; } };
    if (name.endsWith('/rds-signer')) return { Signer: function() { return { async getAuthToken() { if (failAt === 'credential') throw Error('sensitive-canary'); return 'sensitive-canary'; } }; } };
    assert.equal(name, 'node:fs'); return { readFileSync: () => 'sensitive-canary' };
  } });
  for (let i = 0; i < 30 && output.length === 0; i++) await new Promise(resolve => setImmediate(resolve));
  assert.equal(output.length, 1); assert(!JSON.stringify(output).includes('sensitive-canary'));
  assert.equal(output[0].verdict, failAt ? 'failed' : 'observed');
  if (failAt) assert.equal(output[0].phase, failAt);
  else { assert.equal(calls.at(-1), 'ROLLBACK'); assert.equal(output[0].edges[0].grantor, 'other'); }
  assert.equal(closed, ['configuration', 'credential'].includes(failAt) ? 0 : 1);
}
for (const phase of [undefined, 'configuration', 'credential', 'connection', 'observation']) await run(phase);
console.log('Administrator catalogue observation: read-only, safe projection and failed-phase caller fixtures passed.');
