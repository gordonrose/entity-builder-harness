// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.fixture.managed-handler-runtime-api
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Drive the official Lambda runtime client from an isolated loopback Runtime API without replacing the packaged handler.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.command.qualify-managed-handler-image
//     path: scripts/04.deploy/lifecycle/40-package/build-managed-handler-image/qualification.py
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { readdirSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { join } from "node:path";

const [program, mode] = process.argv.slice(2);
assert(["invalid", "valid"].includes(mode));
assert(/^kanbien-(?:core-server-persistence|entity-smoke)-scheduling-(?:dispatch|worker)$/.test(program));
const purpose = program.endsWith("-dispatch") ? "dispatch" : "worker";
const entity = program.startsWith("kanbien-entity-smoke-");
const schema = entity ? "entity_smoke" : "platform";
const username = (entity ? "entity_smoke_scheduling_" : "core_scheduling_") + purpose;
const arn = "arn:aws:sqs:eu-west-1:123456789012:qualification";
const canary = "PRIVATE-MANAGED-RUNTIME-CANARY";
const native = (id, body = "not-json-" + canary) => ({ messageId: id, body, receiptHandle: "private-receipt-" + canary, eventSourceARN: arn });
const durableId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const envelope = JSON.stringify({ id: durableId, idempotencyKey: durableId,
  type: entity ? "entity-smoke.test-entity.purge-expired" : "kanbien-core-server.persistence.scheduling.verify", version: 1,
  enqueuedAt: "2026-11-27T00:00:00.000Z", payload: { outboxEntryId: durableId } });
const stopped = { delivery: null, relayAttempts: 0, published: 0, stopReason: "requested-stop" };
const cases = mode === "invalid" ? [{ name: "configuration-rejection", event: { private: canary }, error: true, remaining: 60_000 }]
  : purpose === "dispatch" ? [
    { name: "initialization-deadline", event: {}, expected: stopped, remaining: 30_000 },
    { name: "warm-deadline", event: { private: canary }, expected: stopped, remaining: 30_000 },
  ] : [
    { name: "initialization-empty-batch", event: { Records: [] }, expected: { batchItemFailures: [] }, remaining: 60_000 },
    { name: "malformed-record-retained", event: { Records: [native("malformed")] }, expected: { batchItemFailures: [{ itemIdentifier: "malformed" }] }, remaining: 60_000 },
    { name: "deadline-record-retained", event: { Records: [native("deadline", envelope)] }, expected: { batchItemFailures: [{ itemIdentifier: "deadline" }] }, remaining: 30_000 },
    { name: "unavailable-database-retained", event: { Records: [native("database", envelope)] }, expected: { batchItemFailures: [{ itemIdentifier: "database" }] }, remaining: 60_000 },
    { name: "oversize-batch-rejected", event: { Records: [native("one"), native("two")] }, error: true, remaining: 60_000 },
    { name: "malformed-event-rejected", event: { private: canary }, error: true, remaining: 60_000 },
    { name: "warm-empty-batch", event: { Records: [] }, expected: { batchItemFailures: [] }, remaining: 60_000 },
  ];
if (mode === "valid") cases.push(
  { name: "preflight-malformed-rejected", event: { kind: "scheduling-preflight/v1", private: canary }, error: true, remaining: 60_000 },
  { name: "preflight-deadline-rejected", event: { kind: "scheduling-preflight/v1" }, error: true, remaining: 20_000 },
  { name: "preflight-unavailable-database-rejected", event: { kind: "scheduling-preflight/v1" }, error: true, remaining: 60_000 },
);
const config = mode === "invalid" ? {} : {
  NODE_ENV: "test", PERSISTENCE_IMPLEMENTATION: "postgresql", PERSISTENCE_POSTGRES_HOST: "127.0.0.1",
  PERSISTENCE_POSTGRES_PORT: "1", PERSISTENCE_POSTGRES_DATABASE: "qualification", PERSISTENCE_POSTGRES_SCHEMA: schema,
  PERSISTENCE_POSTGRES_IAM_AUTHENTICATION_REFERENCE: "arn:aws:rds-db:eu-west-1:123456789012:dbuser:db-qualification/" + username,
  PERSISTENCE_SCHEDULING_DATABASE_USERNAME: username, PERSISTENCE_POSTGRES_IAM_REGION: "eu-west-1",
  PERSISTENCE_LOCAL_QUALIFICATION_IAM_TOKEN: "synthetic-qualification-token",
  SCHEDULING_QUEUE_URL: "https://sqs.eu-west-1.amazonaws.com/123456789012/qualification",
  SCHEDULING_QUEUE_ARN: arn, AWS_REGION: "eu-west-1", AWS_EC2_METADATA_DISABLED: "true",
};
let child, pending, next = 0, finished = 0, failure, output = "", settled = false;
const completed = new Promise((resolve, reject) => { pending = { resolve, reject }; });
const reject = () => { if (!settled) { settled = true; failure = true; pending.reject(Error("runtime-interface-proof-failed")); } };
const timer = setTimeout(reject, 45_000);
const server = createServer((request, response) => {
  try {
    if (request.method === "GET" && request.url === "/2018-06-01/runtime/invocation/next") {
      if (next === cases.length) { response.writeHead(503); response.end(); return; }
      const current = cases[next++];
      response.writeHead(200, { "Content-Type": "application/json", "Lambda-Runtime-Aws-Request-Id": "00000000-0000-4000-8000-" + String(next - 1).padStart(12, "0"),
        "Lambda-Runtime-Deadline-Ms": String(Date.now() + current.remaining),
        "Lambda-Runtime-Client-Context": JSON.stringify({ custom: { scheduling_preflight_operation_id: "c1c6c162-c9c8-4a2f-9ef9-158d8ce66f1f" } }),
        "Lambda-Runtime-Invoked-Function-Arn": "arn:aws:lambda:eu-west-1:123456789012:function:qualification:1" });
      response.end(JSON.stringify(current.event));
      return;
    }
    const matched = /^\/2018-06-01\/runtime\/invocation\/00000000-0000-4000-8000-([0-9]{12})\/(response|error)$/.exec(request.url ?? "");
    if (request.method !== "POST" || !matched || Number(matched[1]) !== finished || finished >= next) throw Error();
    let text = "";
    request.on("data", chunk => { text += chunk; if (text.length > 65536) { reject(); request.destroy(); } });
    request.on("end", () => {
      try {
        const expected = cases[finished], value = JSON.parse(text);
        assert(!text.includes(canary));
        if (expected.error) {
          assert.equal(matched[2], "error"); assert.equal(value.errorMessage, "SCHEDULING_INVOCATION_FAILED");
          assert.equal(value.errorType, "Error");
        } else { assert.equal(matched[2], "response"); assert.deepEqual(value, expected.expected); }
        finished++; response.writeHead(202); response.end();
        if (finished === cases.length && !settled) { settled = true; pending.resolve(); }
      } catch { response.writeHead(500); response.end(); reject(); }
    });
  } catch { response.writeHead(500); response.end(); reject(); }
});

try {
  assert.notEqual(process.getuid(), 0, "qualification must exercise the nonroot runtime");
  assert.throws(() => writeFileSync("/var/task/qualification-must-not-write", "x"), /EROFS|EACCES/);
  writeFileSync("/tmp/qualification-scratch", "owned"); rmSync("/tmp/qualification-scratch");
  for (const top of ["packages", "platform", "apps", "infra"]) {
    const walk = path => {
      let entries; try { entries = readdirSync(path, { withFileTypes: true }); } catch (error) { if (error.code === "ENOENT") return; throw error; }
      for (const entry of entries) {
        assert(![".env", ".git", "secrets", "credentials", "node_modules"].includes(entry.name));
        const file = join(path, entry.name);
        if (entry.isDirectory()) walk(file); else assert(!/\.(?:ts|tsx|pem|key)$/.test(entry.name), "source or private key in runtime payload");
      }
    };
    walk("/var/task/" + top);
  }
  JSON.parse(readFileSync("/var/task/runtime-payload.json", "utf8"));
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  const environment = { ...process.env, ...config, AWS_LAMBDA_RUNTIME_API: "127.0.0.1:" + server.address().port };
  delete environment.NODE_OPTIONS; delete environment.AWS_ACCESS_KEY_ID; delete environment.AWS_SECRET_ACCESS_KEY; delete environment.AWS_SESSION_TOKEN;
  child = spawn("/lambda-entrypoint.sh", ["handler.handler"], { env: environment, stdio: ["ignore", "pipe", "pipe"] });
  for (const stream of [child.stdout, child.stderr]) stream.on("data", chunk => {
    output += chunk.toString(); if (output.length > 2_000_000 || output.includes(canary)) reject();
  });
  child.once("error", reject);
  child.once("exit", () => { if (!settled) reject(); });
  await completed;
  assert.equal(next, cases.length); assert.equal(finished, cases.length);
  assert(!output.includes(canary));
  console.log(JSON.stringify({ schema: "deploy/managed-runtime-invocation/v1", verdict: "passed", program_id: program,
    mode, cases: cases.map(value => value.name), responses: finished, runtime_interface: "official-aws-lambda-client" }));
} catch {
  failure = true;
  console.error(JSON.stringify({ schema: "deploy/managed-runtime-invocation/v1", verdict: "failed", code: "managed-runtime-invocation-failed" }));
} finally {
  clearTimeout(timer);
  if (child) {
    child.kill("SIGTERM");
    await Promise.race([new Promise(resolve => child.once("exit", resolve)), new Promise(resolve => setTimeout(resolve, 2000))]);
    if (child.exitCode === null && child.signalCode === null) child.kill("SIGKILL");
  }
  server.closeAllConnections(); await new Promise(resolve => server.close(resolve));
  process.exitCode = failure ? 1 : 0;
}
