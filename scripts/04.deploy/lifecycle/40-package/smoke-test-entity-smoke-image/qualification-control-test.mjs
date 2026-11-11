// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.qualification-control
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-11"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [security, sre]
//   kind: script
//   purpose: Exercise the qualifier's actual safe CLI and reservation cleanup using an isolated fake Docker executable, never a real engine.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.entity-smoke.composition.wrapper
//     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const fixture = mkdtempSync(join(tmpdir(), "entity-smoke-qualification-control-"));
const reservations = [];
const verifier = "scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs";
const canary = "credential-row-provider-canary";
try {
  const calls = join(fixture, "calls.jsonl"), fake = join(fixture, "docker");
  writeFileSync(fake, "#!" + process.execPath + "\n" + `
const fs=require('node:fs'); const args=process.argv.slice(2); const [kind,operation,name]=args;
const tcp=args.includes('pg_isready')&&args.includes('-h')&&args.includes('127.0.0.1');
fs.appendFileSync(process.env.ENTITY_SMOKE_FIXTURE_CALLS,JSON.stringify({kind,operation,name,tcp})+'\\n');
if(process.env.ENTITY_SMOKE_FIXTURE_STARTUP==='true'){
  if(kind==='info'){console.log('linux');process.exit(0)}
  if(kind==='image'&&operation==='inspect'){console.log(JSON.stringify([{Architecture:'amd64',Os:'linux',Id:'sha256:'+'c'.repeat(64),Config:{User:'nonroot',Labels:{'org.opencontainers.image.revision':'b'.repeat(40)},Env:[]}}]));process.exit(0)}
  if(kind==='exec'&&args.includes('pg_isready')){
    // Unix readiness would report the temporary initialization server. Only
    // the final TCP server permits the subsequent SQL version observation.
    if(tcp)fs.writeFileSync(process.env.ENTITY_SMOKE_FIXTURE_CALLS+'.tcp','ready');
    process.exit(0);
  }
  if(kind==='exec'&&args.includes('SHOW server_version_num')){
    if(!fs.existsSync(process.env.ENTITY_SMOKE_FIXTURE_CALLS+'.tcp'))process.exit(2);
    console.log('180003');process.exit(0);
  }
  if(kind==='exec'&&args.includes('SELECT pg_reload_conf()')){console.log('t');process.exit(0)}
  if(kind==='run'||kind==='exec'||kind==='cp'||operation==='create')process.exit(0);
}
if(process.env.ENTITY_SMOKE_FIXTURE_UNOBSERVABLE==='true'){process.stderr.write('${canary}');process.exit(1)}
if(operation!=='inspect')process.exit(9);
const messages={container:'No such container: '+name,network:'network '+name+' not found',volume:'get '+name+': no such volume'};
process.stderr.write('Error response from daemon: '+messages[kind]+'\\n');process.exit(1);
`, { mode: 0o700 });
  function run(args, unavailable = false, startup = false) {
    const result = spawnSync(process.execPath, [verifier, ...args], { encoding: "utf8", timeout: 10_000,
      env: { ...process.env, PATH: fixture + ":" + process.env.PATH, ENTITY_SMOKE_FIXTURE_CALLS: calls, ENTITY_SMOKE_FIXTURE_UNOBSERVABLE: String(unavailable), ENTITY_SMOKE_FIXTURE_STARTUP: String(startup) } });
    assert.equal(result.error, undefined); assert.equal(result.signal, null);
    assert(!(result.stdout + result.stderr).includes(canary));
    return result;
  }
  const invalid = run(["--invalid", canary]);
  assert.equal(invalid.status, 1);
  assert.deepEqual(JSON.parse(invalid.stderr), { schema: "deploy/entity-smoke-image-qualification/v1", verdict: "failed", code: "ENTITY_SMOKE_IMAGE_PROOF_NOT_CONFIRMED", phase: "arguments", effect: "not-started" });
  assert(!existsSync(calls));
  function reservation(changes = {}) {
    const directory = mkdtempSync(join(tmpdir(), "entity-smoke-image-")); reservations.push(directory);
    const network = "entity-smoke-qualification-" + "a".repeat(24);
    const value = { schema: "deploy/entity-smoke-image-resources/v1", source_revision: "b".repeat(40), local_image_id: "sha256:" + "c".repeat(64), containers: [network + "-task", network + "-database", network + "-restored", network + "-server"], networks: [network], volumes: [network + "-certs", network + "-source-data", network + "-restored-data"], ...changes };
    const path = join(directory, "resource-reservation.json"); writeFileSync(path, JSON.stringify(value), { mode: 0o600 });
    return { directory, path };
  }
  const unsafe = reservation({ containers: [canary] });
  assert.equal(run(["--cleanup-reservation", unsafe.path]).status, 1);
  assert(!existsSync(calls)); assert(existsSync(unsafe.path));
  const accepted = reservation();
  const removed = run(["--cleanup-reservation", accepted.path]);
  assert.equal(removed.status, 0, removed.stderr);
  assert.deepEqual(JSON.parse(removed.stdout), { schema: "deploy/entity-smoke-image-cleanup/v1", verdict: "passed", qualification_evidence: false });
  assert(!existsSync(accepted.directory));
  const first = readFileSync(calls, "utf8").trim().split("\n").map(JSON.parse);
  assert.equal(first.length, 8); assert(first.every(call => call.operation === "inspect"));
  const uncertain = reservation();
  const blocked = run(["--cleanup-reservation", uncertain.path], true);
  assert.equal(blocked.status, 1);
  assert(blocked.stderr.includes("ENTITY_SMOKE_DISPOSABLE_CLEANUP_NOT_CONFIRMED"));
  assert(!blocked.stdout.includes('"verdict":"passed"'));
  assert(existsSync(uncertain.path), "unobservable engine state must preserve the recovery reservation");
  const all = readFileSync(calls, "utf8").trim().split("\n").map(JSON.parse);
  assert(all.every(call => call.operation === "inspect"), "an engine error must not be treated as absence or authorize removal");
  writeFileSync(join(fixture, 'git'), '#!' + process.execPath + '\n' + `
const args=process.argv.slice(2);
if(args[0]==='rev-parse'&&args[1]==='HEAD'){console.log('b'.repeat(40));process.exit(0)}
if(args[0]==='status')process.exit(0);
process.exit(2);
`, { mode: 0o700 });
  const startup = run([], false, true);
  assert.equal(startup.status, 1, 'this fake scenario deliberately stops at administration, never claims qualification');
  const startupFailure = JSON.parse(startup.stderr);
  assert.equal(startupFailure.phase, 'provider-administration-preflight', 'initialization readiness must reach the final PostgreSQL server before SQL');
  assert(!startup.stderr.includes('CLEANUP_NOT_CONFIRMED'));
  const startupCalls = readFileSync(calls, 'utf8').trim().split('\n').map(JSON.parse).slice(all.length);
  assert(startupCalls.some(call => call.kind === 'exec' && call.tcp), 'the actual qualifier must invoke TCP readiness');
  console.log(JSON.stringify({ verdict: "passed", scope: "entity-smoke-qualification-control", real_engine: false, cases: ["safe-arguments", "reject-unowned-reservation", "exact-absence-cleanup", "cleanup-not-qualification", "unobservable-not-absence", "retain-uncertain-reservation", "final-tcp-not-initialization-socket"] }));
} finally {
  for (const path of reservations) rmSync(path, { recursive: true, force: true });
  rmSync(fixture, { recursive: true });
}
