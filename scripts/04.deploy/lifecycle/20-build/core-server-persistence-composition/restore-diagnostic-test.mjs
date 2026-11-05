#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.packaged-persistence-connection-diagnostic
//   version: 2
//   status: active
//   created_on: "2026-10-26"
//   updated_on: "2026-11-04"
//   layer: 04.deploy
//   domain: persistence.diagnostics
//   disciplines: [security, sre]
//   kind: script
//   purpose: Run the actual packaged restore entrypoint and real pg driver against a disposable TLS protocol fixture, proving diagnostic versus recovery results.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
import assert from "node:assert/strict";
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { createSecureContext, TLSSocket } from "node:tls";
import { createRequire } from "node:module";

import { fixtureRuntime } from "./fixture-runtime.mjs";
const compiled = fixtureRuntime(process.argv[2]);
const temporary = mkdtempSync(join(tmpdir(), "packaged-restore-diagnostic-"));
const canary = "synthetic-diagnostic-wire-canary";
const sockets = new Set();
let rejectAuthentication = false;
const queries = [];
function packet(type, payload) { const head = Buffer.alloc(5); head[0] = type.charCodeAt(0); head.writeInt32BE(payload.length + 4, 1); return Buffer.concat([head, payload]); }
const ready = () => Buffer.concat([packet("R", Buffer.from([0, 0, 0, 0])), packet("Z", Buffer.from("I"))]);
async function child(environment, preload) {
  return new Promise((resolveChild, reject) => {
    const processChild = spawn(process.execPath, ["--require", preload, join(compiled, "kanbien-core-server-persistence-restore-verifier.main.js")], { env: environment, stdio: ["ignore", "pipe", "pipe"] });
    let output = "";
    const timer = setTimeout(() => { processChild.kill("SIGKILL"); reject(new Error("packaged diagnostic fixture deadline")); }, 15_000);
    for (const stream of [processChild.stdout, processChild.stderr]) stream.on("data", (value) => { output += value; if (output.length > 65_536) processChild.kill("SIGKILL"); });
    processChild.once("error", reject);
    processChild.once("close", (code) => { clearTimeout(timer); resolveChild({ code, output }); });
  });
}
let server;
try {
  const key = join(temporary, "fixture.key"), certificate = join(temporary, "fixture.crt");
  assert.equal(spawnSync("openssl", ["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", certificate, "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost", "-days", "1"], { stdio: "pipe", timeout: 10_000 }).status, 0);
  let context = createSecureContext({ key: readFileSync(key), cert: readFileSync(certificate) });
  server = createServer((socket) => {
    sockets.add(socket); socket.on("error", () => undefined); socket.once("close", () => sockets.delete(socket));
    socket.once("data", () => {
      socket.write("S");
      const secure = new TLSSocket(socket, { isServer: true, secureContext: context });
      secure.on("error", () => undefined);
      let buffered = Buffer.alloc(0), state = "startup";
      secure.on("data", (data) => {
        buffered = Buffer.concat([buffered, data]);
        while (buffered.length >= (state === "startup" ? 4 : 5)) {
          const length = state === "startup" ? buffered.readInt32BE(0) : buffered.readInt32BE(1) + 1;
          if (length < 4 || length > 65_536) { secure.destroy(); return; }
          if (buffered.length < length) return;
          const message = buffered.subarray(0, length); buffered = buffered.subarray(length);
          if (state === "startup") { secure.write(packet("R", Buffer.from([0, 0, 0, 3]))); state = "password"; }
          else if (state === "password") {
            if (rejectAuthentication) { secure.end(packet("E", Buffer.from(`SFATAL\0C28P01\0M${canary}\0\0`))); return; }
            secure.write(ready()); state = "query";
          } else if (message[0] === 81) {
            queries.push(message.subarray(5, -1).toString());
            secure.write(Buffer.concat([packet("C", Buffer.from("SELECT 1\0")), packet("Z", Buffer.from("I"))]));
          }
        }
      });
    });
  });
  await new Promise((done, reject) => { server.once("error", reject); server.listen(0, "localhost", done); });
  const preload = join(temporary, "ca-path.cjs");
  // Only the filesystem adapter is redirected: the shipped path validator,
  // wrapper, credential provider, pool, parser and TLS stack execute unchanged.
  writeFileSync(preload, `const fs=require('node:fs'); const original=fs.readFileSync; fs.readFileSync=function(path,...args){return original.call(this,path==='/app/assets/fixture.crt'?${JSON.stringify(certificate)}:path,...args)};`);
  const environment = { ...process.env, NODE_PATH: resolve("node_modules"), NODE_ENV: "test", PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: canary, PERSISTENCE_POSTGRES_HOST: "localhost", PERSISTENCE_POSTGRES_PORT: String(server.address().port), PERSISTENCE_POSTGRES_DATABASE: "kanbienpersistence", PERSISTENCE_POSTGRES_SCHEMA: "platform", PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1", PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-FIXTURE/core_runtime", PERSISTENCE_RESTORE_RUNTIME_DATABASE_USERNAME: "core_runtime", PERSISTENCE_POSTGRES_CA_PATH: "/app/assets/fixture.crt", PERSISTENCE_ACCEPTANCE_RECORD_ID: "core-persistence-diagnostic-fixture", PERSISTENCE_ACCEPTANCE_FACT_DIGEST: "a".repeat(64) };
  for (const key of Object.keys(environment)) if (key.startsWith("AWS_") || key.startsWith("PERSISTENCE_ADMINISTRATOR")) delete environment[key];
  for (const [mode, rejected, delayedToken, verdict, code, exit] of [["connection", false, false, "diagnosed", "KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED", 0], ["connection", false, true, "diagnosed", "KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED", 0], ["connection", true, false, "diagnostic-failed", "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED", 1], [undefined, true, false, "rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED", 1]]) {
    rejectAuthentication = rejected;
    const env = { ...environment }; if (mode !== undefined) env.PERSISTENCE_RESTORE_DIAGNOSTIC_MODE = mode; else delete env.PERSISTENCE_RESTORE_DIAGNOSTIC_MODE;
    if (delayedToken) env.PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN_DELAY_MS = "5500";
    const result = await child(env, preload);
    assert.equal(result.output.includes(canary), false, "wire error/token canary must not escape the real entrypoint");
    assert.equal(result.code, exit, "entrypoint exit status must preserve its result");
    const value = JSON.parse(result.output.trim());
    assert.equal(value.schema, "deploy/persistence-restore-verifier-result/v2"); assert.equal(value.verdict, verdict); assert.equal(value.code, code);
    if (rejected) { assert.equal(value.execution.phase, "pool_connect"); assert.equal(value.execution.classification, "authentication_rejected"); assert.equal(value.execution.code_status, "recognized"); assert.ok(value.execution.elapsed_ms >= 0); }
  }
  assert.deepEqual(queries, ["SELECT 1", "SELECT 1"], "each successful diagnostic must issue only its bounded read, never record verification or mutation");
  rejectAuthentication = false;
  await restoreCleanupRegression(environment, certificate);
  await maintenanceCheckedValueRegression(environment, certificate);
  // Trust the fixture certificate but give it a different peer identity. This
  // exercises the actual TLS preflight and packaged result, not a synthetic code.
  assert.equal(spawnSync("openssl", ["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", certificate, "-subj", "/CN=fixture.invalid", "-addext", "subjectAltName=DNS:fixture.invalid", "-days", "1"], { stdio: "pipe", timeout: 10_000 }).status, 0);
  context = createSecureContext({ key: readFileSync(key), cert: readFileSync(certificate) });
  const mismatch = await child({ ...environment, PERSISTENCE_RESTORE_DIAGNOSTIC_MODE: "connection" }, preload);
  const mismatchRecord = JSON.parse(mismatch.output.trim());
  assert.equal(mismatch.code, 1);
  assert.equal(mismatchRecord.code, "KANBIEN_CORE_PERSISTENCE_RESTORE_TLS_TRUST_INVALID");
  assert.equal(mismatchRecord.execution.phase, "tls_probe");
  assert.equal(mismatchRecord.diagnostic.definitionVersion, 2);
  assert.equal(mismatchRecord.diagnostic.detail.operation, "restore_verification");
  assert.deepEqual(mismatchRecord.related_diagnostics.map((record) => record.detail.reason), ["hostname-mismatch"]);
  assert.equal(mismatch.output.includes("fixture.invalid"), false);
  assert.equal(mismatch.output.includes(canary), false);
  assert.deepEqual(queries, ["SELECT 1", "SELECT 1"], "failed TLS preflight sends no query");
  console.log("Packaged restore diagnostic CLI and real-driver TLS protocol tests passed.");
} finally {
  for (const socket of sockets) socket.destroy();
  if (server) await new Promise((done) => server.close(done));
  rmSync(temporary, { recursive: true, force: true });
}

async function maintenanceCheckedValueRegression(environment, certificate) {
  const require = createRequire(join(compiled, "maintenance-checked-values.cjs"));
  const connection = require(join(compiled, "platform/adapters/aws/persistence/postgresql/src/connection.js"));
  const configuration = require(join(compiled, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js"));
  const restore = require(join(compiled, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.js"));
  const checks = require(join(compiled, "packages/core/src/config/domain/validation/settings.js"));
  const savedPool = connection.createNodePostgreSqlTokenConnectionPool, savedAuthority = configuration.persistenceCertificateAuthorityResult;
  const savedCheck = checks.validateConfigRequirements, savedLog = console.log, savedError = console.error, savedExit = process.exitCode;
  const checkedId = "core-persistence-checked-value", checkedDigest = "b".repeat(64);
  let checksUsed = 0, queriesUsed = 0;
  const output = [];
  checks.validateConfigRequirements = (source, requirements) => {
    const checked = savedCheck(source, requirements);
    if (!checked.ok || !requirements.some(item => item.setting === "verification.expected-record-id")) return checked;
    checksUsed++;
    return { ok: true, value: { ...checked.value, "verification.expected-record-id": checkedId, "verification.expected-fingerprint": checkedDigest } };
  };
  configuration.persistenceCertificateAuthorityResult = () => ({ ok: true, value: readFileSync(certificate, "utf8") });
  console.log = console.error = line => output.push(JSON.parse(line));
  try {
    for (const mode of [undefined, "", " \t", " connection ", false, 1, "connection"]) {
      let count = 0, releases = 0, ends = 0;
      const observed = [];
      const controls = ["PERSISTENCE_RESTORE_DIAGNOSTIC_MODE", "PERSISTENCE_ACCEPTANCE_RECORD_ID", "PERSISTENCE_ACCEPTANCE_FACT_DIGEST"];
      const supplied = new Proxy({ ...environment, PERSISTENCE_RESTORE_DIAGNOSTIC_MODE: mode,
        ...(mode === "connection" ? { PERSISTENCE_ACCEPTANCE_RECORD_ID: undefined, PERSISTENCE_ACCEPTANCE_FACT_DIGEST: "ignored-malformed-value" } : {}) }, {
        get(target, key) { if (controls.includes(key)) observed.push(key); return target[key]; },
      });
      const client = { async query(statement) {
        count++; queriesUsed++;
        if (mode === "connection") { assert.deepEqual(statement, { text: "SELECT 1" }); return { rows: [] }; }
        assert.deepEqual(statement.values, [checkedId], "the actual SELECT must use the returned checked ID, not the supplied ID");
        return { rows: [{ record_id: checkedId, fact_digest: checkedDigest }] };
      }, release() { releases++; } };
      connection.createNodePostgreSqlTokenConnectionPool = () => ({ async connect() { return client; }, async end() { ends++; } });
      output.length = 0; process.exitCode = 0;
      await restore.runKanbienCoreServerPersistenceRestoreVerifier(supplied);
      assert.equal(process.exitCode, 0);
      assert.equal(count, 1); assert.equal(releases, 1); assert.equal(ends, 1);
      assert.deepEqual(observed.slice(-3), controls, "mode then expected ID/fingerprint remain the last control reads; no unchecked reread");
      assert.deepEqual(output, [{ schema: "deploy/persistence-restore-verifier-result/v2", verdict: mode === "connection" ? "diagnosed" : "accepted",
        code: mode === "connection" ? "KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED" : "KANBIEN_CORE_PERSISTENCE_RESTORED_RECORD_RETRIEVED" }]);
    }
    assert.equal(checksUsed, 6); assert.equal(queriesUsed, 7);
  } finally {
    connection.createNodePostgreSqlTokenConnectionPool = savedPool; configuration.persistenceCertificateAuthorityResult = savedAuthority;
    checks.validateConfigRequirements = savedCheck; console.log = savedLog; console.error = savedError; process.exitCode = savedExit;
  }
}

async function restoreCleanupRegression(environment, certificate) {
  const require = createRequire(join(compiled, "restore-cleanup-test.cjs")), entrypoints = join(compiled, "infra/04.deploy/03.product/entrypoints");
  const connection = require(join(compiled, "platform/adapters/aws/persistence/postgresql/src/connection.js"));
  const configuration = require(join(entrypoints, "kanbien-core-server-persistence-configuration.js"));
  const restore = require(join(entrypoints, "kanbien-core-server-persistence-restore-verifier.main.js"));
  const originalPool = connection.createNodePostgreSqlTokenConnectionPool, originalAuthority = configuration.persistenceCertificateAuthorityResult;
  const originalLog = console.log, originalError = console.error, originalExit = process.exitCode;
  const source = (offset) => Array.from({ length: 9 }, (_, ordinal) => ({ schema: "core/diagnostic-record/v1", code: "core.persistence.in-memory-boundary-failed", definitionVersion: 1,
    detail: { operation: "initialize", phase: "get-id", reason: "boundary-threw", effect: "write-not-reached", ordinal: offset + ordinal } }));
  const first = source(0), second = source(20);
  const failure = (records) => Object.freeze(Object.assign(new Error(canary), { diagnosticRecord: records[0], relatedDiagnosticRecords: records.slice(1) }));
  const body = failure(first), cleanup = failure(second), output = [], events = [];
  const capture = (line) => { events.push("output"); output.push(JSON.parse(line)); };
  console.log = console.error = capture;
  configuration.persistenceCertificateAuthorityResult = () => ({ ok: true, value: readFileSync(certificate, "utf8") });
  try {
    for (const bodyFails of [false, true]) for (const ending of ["none", "release", "sync-end", "rejected-end"]) {
      output.length = events.length = 0; process.exitCode = 73;
      let connects = 0, releases = 0, ends = 0, queryCalls = 0;
      const client = { async query(statement) { assert.equal(this, client); queryCalls++; assert.deepEqual(statement, { text: "SELECT 1" }); if (bodyFails) throw body; return { rows: [] }; }, release() { assert.equal(this, client); events.push("release"); releases++; if (ending === "release") throw cleanup; } };
      const pool = { async connect() { assert.equal(this, pool); connects++; return client; }, end() { assert.equal(this, pool); events.push("end"); ends++; if (ending === "sync-end") throw cleanup; return ending === "rejected-end" ? Promise.reject(cleanup) : Promise.resolve(); } };
      connection.createNodePostgreSqlTokenConnectionPool = () => pool;
      const run = () => restore.runKanbienCoreServerPersistenceRestoreVerifier({ ...environment, PERSISTENCE_RESTORE_DIAGNOSTIC_MODE: "connection" });
      if (ending === "release") await assert.rejects(run, (error) => error === cleanup); else await run();
      assert.equal(connects, 1); assert.equal(queryCalls, 1); assert.equal(releases, 1); assert.equal(ends, ending === "release" ? 0 : 1, "throwing release still skips end");
      assert.equal(events.indexOf("output") < events.indexOf("release"), true, "original result remains the first serialization before cleanup");
      assert.equal(output[0].schema, "deploy/persistence-restore-verifier-result/v2");
      assert.equal(output[0].verdict, bodyFails ? "diagnostic-failed" : "diagnosed");
      assert.equal(output[0].code, bodyFails ? "KANBIEN_CORE_PERSISTENCE_RESTORE_QUERY_UNAVAILABLE" : "KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED");
      if (bodyFails) assert.deepEqual([output[0].diagnostic, ...output[0].related_diagnostics], first); else assert.equal(output[0].diagnostic, undefined);
      assert.equal(process.exitCode, bodyFails ? 1 : 73);
      const observed = output.filter((value) => value.message === "platform.diagnostic.observed");
      const boundary = ending === "release" ? { operation: "transaction-client", phase: "invocation", boundary: "release", condition: "threw", effect: "not-assessed" }
        : { operation: "connection-pool", phase: ending === "sync-end" ? "invocation" : "completion", boundary: "end", condition: ending === "sync-end" ? "threw" : "rejected", effect: "not-assessed" };
      assert.deepEqual(observed.map((value) => value.fields.diagnostic), ending === "none" ? [] : [{ schema: "core/diagnostic-record/v1", code: "persistence.boundary-observed", definitionVersion: 1, detail: boundary }, ...second]);
      assert(observed.every((value) => value.fields.operation === "restore-verification" && value.fields.stage === "recovery"));
      assert.equal(JSON.stringify(output).includes(canary), false);
    }
    const serialization = Object.freeze(new Error(canary)); let serializations = 0, releases = 0, ends = 0;
    console.log = console.error = (line) => { const value = JSON.parse(line); if (value.schema === "deploy/persistence-restore-verifier-result/v2") { serializations++; throw serialization; } output.push(value); };
    connection.createNodePostgreSqlTokenConnectionPool = () => ({ async connect() { return { async query() { return { rows: [] }; }, release() { releases++; } }; }, end() { ends++; throw cleanup; } });
    process.exitCode = 73;
    await assert.rejects(() => restore.runKanbienCoreServerPersistenceRestoreVerifier({ ...environment, PERSISTENCE_RESTORE_DIAGNOSTIC_MODE: "connection" }), (error) => error === serialization);
    assert.equal(serializations, 2); assert.equal(releases, 1); assert.equal(ends, 1); assert.equal(process.exitCode, 73, "swallowed sync end cannot return from finally and replace pending serialization failure");
  } finally { connection.createNodePostgreSqlTokenConnectionPool = originalPool; configuration.persistenceCertificateAuthorityResult = originalAuthority; console.log = originalLog; console.error = originalError; process.exitCode = originalExit; }
}
