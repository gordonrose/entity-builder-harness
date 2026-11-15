// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.administrator-observation
//   version: 2
//   status: draft
//   created_on: "2026-11-11"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Prove the retired administrator observation program refuses execution without reading credentials or invoking dependencies.
//   portability: {class: internal, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.library.entity-smoke.administrator-observation
//     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/administrator-observation.js

import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import vm from 'node:vm';

const target = new URL('./administrator-observation.js', import.meta.url);
const source = readFileSync(target, 'utf8');
const expected = {
  schema: 'deploy/entity-smoke-administrator-observation/v1',
  verdict: 'blocked', condition: 'administrator-observation-retired', effect: 'not-started'
};
const output = [];
const processStub = { get env() { throw new Error('credentials accessed'); } };
vm.runInNewContext(source, {
  process: processStub,
  require() { throw new Error('dependency invoked'); },
  console: { log(line) { output.push(JSON.parse(line)); }, error() { assert.fail('unexpected error channel'); } }
});
assert.deepEqual(output, [expected]);
assert.equal(processStub.exitCode, 1);
const result = spawnSync(process.execPath, [target.pathname, '--execute', 'private-argument-canary'], {
  encoding: 'utf8', timeout: 5000, env: { PERSISTENCE_ADMINISTRATOR_CREDENTIALS: 'private-credential-canary' }
});
assert.equal(result.error, undefined);
assert.equal(result.status, 1);
assert.equal(result.stderr, '');
assert.deepEqual(JSON.parse(result.stdout), expected);
assert(!result.stdout.includes('canary'));
console.log('Retired administrator observation: no dependency/credential effects and actual CLI refusal passed.');
