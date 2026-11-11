// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.administrator-recovery
//   version: 1
//   status: draft
//   created_on: "2026-11-11"
//   updated_on: "2026-11-11"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Prove exact one-link recovery, rollback and uncertainty reporting with controlled database clients.
//   portability: {class: internal, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.library.entity-smoke.administrator-recovery
//     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-recovery.js
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
const source = readFileSync(new URL('./administrator-recovery.js', import.meta.url), 'utf8');
const initial = [
  { role: 'entity_smoke_migration', member: 'core_migration', grantor: 'rdsadmin', admin_option: false, inherit_option: false, set_option: true },
  { role: 'rds_iam', member: 'entity_smoke_migration', grantor: 'rdsadmin', admin_option: false, inherit_option: false, set_option: true },
  { role: 'rds_iam', member: 'entity_smoke_runtime', grantor: 'rdsadmin', admin_option: false, inherit_option: false, set_option: true },
  { role: 'rds_superuser', member: 'core_migration', grantor: 'rdsadmin', admin_option: false, inherit_option: true, set_option: true },
];
async function run(failure, ownerAllowed = true) {
  let removed = false, connections = 0, closed = 0; const calls = [], output = [];
  const context = { process: { env: { PERSISTENCE_POSTGRES_HOST: 'kanbien-core-platform-persistence.cl62wkc0w898.eu-west-1.rds.amazonaws.com', PERSISTENCE_POSTGRES_DATABASE: 'kanbienpersistence', PERSISTENCE_POSTGRES_SCHEMA: 'entity_smoke', PERSISTENCE_ADMINISTRATOR_CREDENTIALS: JSON.stringify({ username: 'core_migration', password: 'sensitive-canary' }) } },
    console: { log: line => output.push(JSON.parse(line)), error: line => output.push(JSON.parse(line)) },
    require(name) {
      if (name.endsWith('/pg')) return { Client: function(options) {
        const ordinal = connections++;
        assert.equal(options.user, 'core_migration'); assert.equal(options.ssl.rejectUnauthorized, true);
        assert.equal(options.password, ordinal ? 'sensitive-canary' : 'token-canary');
        return { async connect() { if (ordinal && failure === 'password') throw Error('sensitive-canary'); }, async end() { closed++; }, async query(sql) {
          calls.push(sql);
          assert(!/^(INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|GRANT)\b/.test(sql));
          if (sql.startsWith('SELECT current_user')) return { rows: [{ administrator: true, iam: removed ? failure === 'still-member' : true }] };
          if (sql.startsWith('SELECT r.rolname')) return { rows: failure === 'edges' ? [] : removed ? initial.slice(1) : initial };
          if (sql.startsWith('SELECT md5')) return { rows: [{ digest: 'a'.repeat(32) }] };
          if (sql.startsWith('REVOKE')) {
            assert.equal(sql, 'REVOKE entity_smoke_migration FROM core_migration');
            if (failure === 'revoke') throw Error('sensitive-canary');
            removed = true;
          }
          if (sql === 'SET LOCAL ROLE entity_smoke_migration' && removed && !ownerAllowed) throw Object.assign(Error('sensitive-canary'), { code: '42501' });
          if (sql === 'COMMIT' && failure === 'commit') throw Error('sensitive-canary');
          if (sql === 'ROLLBACK') removed = false;
          return { rows: [] };
        } };
      } };
      if (name.endsWith('/rds-signer')) return { Signer: function(options) { assert.equal(options.username, 'core_migration'); return { async getAuthToken() { return 'token-canary'; } }; } };
      assert.equal(name, 'node:fs'); return { readFileSync: () => 'certificate-canary' };
    } };
  vm.runInNewContext(source, context);
  for (let n = 0; n < 60 && !output.length; n++) await new Promise(resolve => setImmediate(resolve));
  assert.equal(output.length, 1); assert(!JSON.stringify(output).includes('canary'));
  assert.equal(output[0].verdict, failure ? 'failed' : 'recovered');
  assert.equal(calls.filter(sql => sql.startsWith('REVOKE')).length, failure === 'edges' ? 0 : 1);
  assert.equal(closed, connections);
  if (!failure) { assert.equal(output[0].password_reconnected, true); assert.equal(output[0].owner_selection_without_membership, ownerAllowed); assert.equal(connections, 2); }
  if (['edges', 'revoke', 'still-member'].includes(failure)) { assert.equal(calls.at(-1), 'ROLLBACK'); assert(!calls.includes('COMMIT')); assert.equal(output[0].effect, 'rolled-back'); }
  if (failure === 'commit') { assert.equal(output[0].effect, 'commit-uncertain'); assert.equal(calls.at(-1), 'COMMIT'); assert.equal(connections, 1); }
  if (failure === 'password') { assert.equal(output[0].effect, 'membership-removed'); assert.equal(output[0].phase, 'password-reconnection'); }
}
await run(undefined, true); await run(undefined, false);
for (const failure of ['edges', 'revoke', 'still-member', 'commit', 'password']) await run(failure);
console.log('Administrator recovery caller fixtures passed: exact edge, rollback, no replay, reconnect and safe uncertainty.');
