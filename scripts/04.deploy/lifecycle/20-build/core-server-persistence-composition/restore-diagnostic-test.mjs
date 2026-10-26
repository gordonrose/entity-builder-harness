#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.packaged-persistence-connection-diagnostic
//   version: 1
//   status: active
//   created_on: "2026-10-26"
//   updated_on: "2026-10-26"
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

const compiled = resolve(process.argv[2]);
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
  const context = createSecureContext({ key: readFileSync(key), cert: readFileSync(certificate) });
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
  for (const [mode, rejected, verdict, code, exit] of [["connection", false, "diagnosed", "KANBIEN_CORE_PERSISTENCE_CONNECTION_DIAGNOSED", 0], ["connection", true, "diagnostic-failed", "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED", 1], [undefined, true, "rejected", "KANBIEN_CORE_PERSISTENCE_RESTORE_AUTHENTICATION_REJECTED", 1]]) {
    rejectAuthentication = rejected;
    const env = { ...environment }; if (mode !== undefined) env.PERSISTENCE_RESTORE_DIAGNOSTIC_MODE = mode; else delete env.PERSISTENCE_RESTORE_DIAGNOSTIC_MODE;
    const result = await child(env, preload);
    assert.equal(result.output.includes(canary), false, "wire error/token canary must not escape the real entrypoint");
    assert.equal(result.code, exit, "entrypoint exit status must preserve its result");
    const value = JSON.parse(result.output.trim());
    assert.equal(value.schema, "deploy/persistence-restore-verifier-result/v2"); assert.equal(value.verdict, verdict); assert.equal(value.code, code);
    if (rejected) { assert.equal(value.execution.phase, "pool_connect"); assert.equal(value.execution.classification, "authentication_rejected"); assert.equal(value.execution.code_status, "recognized"); assert.ok(value.execution.elapsed_ms >= 0); }
  }
  assert.deepEqual(queries, ["SELECT 1"], "diagnosis must issue only its bounded read, never record verification or mutation");
  console.log("Packaged restore diagnostic CLI and real-driver TLS protocol tests passed.");
} finally {
  for (const socket of sockets) socket.destroy();
  if (server) await new Promise((done) => server.close(done));
  rmSync(temporary, { recursive: true, force: true });
}
