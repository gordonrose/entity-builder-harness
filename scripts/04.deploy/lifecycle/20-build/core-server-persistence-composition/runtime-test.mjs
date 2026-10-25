#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-composition-runtime
//   version: 2
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-25"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: script
//   purpose: Prove the persistence-capable core-server composition keeps liveness separate from injected dependency readiness and exposes only safe server-mediated acceptance outcomes.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh

import { request as httpRequest } from "node:http";
import { join } from "node:path";

const buildOutput = process.argv[2];
if (typeof buildOutput !== "string" || buildOutput.length === 0) {
  throw new Error("Usage: runtime-test.mjs <compiled-output-directory>");
}

const program = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.js")));
const serverMain = await import(pathToFileUrl(join(buildOutput, "platform/server/src/main.js")));
const verifier = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.js")));
const identityLifecycle = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.js")));
const releaseIdentity = { sourceCommitSha: "local-persistence-composition-proof-2026.10.23" };
const recordId = "core-persistence-acceptance-0001";
const factDigest = "a".repeat(64);

await proveUnavailableDependency();
await proveAvailableDependency();
await proveHealthVerifierModes();
await proveRuntimeIdentityRevocationAndRestoration();

console.log("Core-server persistence composition local runtime proof passed.");

async function proveUnavailableDependency() {
  const fake = fakePersistence({ readiness: "not-ready", create: "unavailable", read: "unavailable" });
  const started = await start(fake);
  try {
    assertStatus(await request(started.handle.port, "GET", "/livez"), 200, "liveness must remain live while persistence is unavailable");
    assertStatus(await request(started.handle.port, "GET", "/readyz"), 503, "readiness must report the unavailable persistence dependency");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", acceptanceRequest()), 503, { outcome: "not-confirmed" }, "unavailable persistence must return only a controlled outcome");
  } finally {
    await started.close();
  }
  if (!fake.closed) throw new Error("Core-server shutdown did not close the injected persistence runtime.");
}

async function proveAvailableDependency() {
  const fake = fakePersistence({ readiness: "ready", create: "created", read: "found" });
  const started = await start(fake);
  try {
    assertStatus(await request(started.handle.port, "GET", "/livez"), 200, "liveness must be live when persistence is ready");
    assertStatus(await request(started.handle.port, "GET", "/readyz"), 200, "readiness must be ready when persistence is ready");
    assertJson(await request(started.handle.port, "GET", "/internal/release-verification"), 200, { release: releaseIdentity }, "candidate must retain bootstrap release verification");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", acceptanceRequest()), 201, { outcome: "created" }, "server-mediated acceptance create must expose a stable result");
    assertJson(await request(started.handle.port, "GET", `/internal/persistence-acceptance?record_id=${recordId}`), 200, { outcome: "found", record: { id: recordId, factDigest }, release: releaseIdentity }, "server-mediated acceptance read must expose only a stable result and release identity");
    assertJson(await request(started.handle.port, "DELETE", `/internal/persistence-acceptance?record_id=${recordId}`), 200, { outcome: "deleted" }, "server-mediated cleanup must be explicit and bounded");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance", {}), 400, { outcome: "invalid-request" }, "invalid persistence requests must not reach the runtime");
    assertStatus(await request(started.handle.port, "GET", "/smoke/product"), 404, "composition must not mount product functionality");
  } finally {
    await started.close();
  }
  if (!fake.closed) throw new Error("Core-server shutdown did not close the injected persistence runtime.");
}

async function proveHealthVerifierModes() {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async (url) => ({ status: String(url).endsWith("/livez") ? 200 : 503, ok: String(url).endsWith("/livez"), json: async () => undefined });
    const unready = await captureConsole(() => verifier.runKanbienCoreServerPersistenceVerifier({
      PERSISTENCE_VERIFIER_MODE: "health-unready",
      KANBIEN_PRIVATE_PERSISTENCE_URL: "http://core-server-persistence.kanbien-core-platform.internal:3000",
    }));
    if (!unready.output.includes("KANBIEN_CORE_PERSISTENCE_LIVE_NOT_READY") || unready.exitCode !== 0) throw new Error("Health verifier did not prove live-but-not-ready safely.");
    globalThis.fetch = async () => ({ status: 200, ok: true, json: async () => undefined });
    const ready = await captureConsole(() => verifier.runKanbienCoreServerPersistenceVerifier({
      PERSISTENCE_VERIFIER_MODE: "health-ready",
      KANBIEN_PRIVATE_PERSISTENCE_URL: "http://core-server-persistence.kanbien-core-platform.internal:3000",
    }));
    if (!ready.output.includes("KANBIEN_CORE_PERSISTENCE_HEALTHY") || ready.exitCode !== 0) throw new Error("Health verifier did not prove recovered readiness safely.");
  } finally {
    globalThis.fetch = originalFetch;
  }
}

async function proveRuntimeIdentityRevocationAndRestoration() {
  const queries = [];
  await identityLifecycle.revokeRuntimeAccess({ query: async (statement) => { queries.push(statement); return { rows: statement.text.includes("pg_terminate_backend") ? [{ terminated: true }] : [] }; } }, "core_runtime");
  if (queries.length !== 3 || !queries[0].text.includes('REVOKE rds_iam FROM "core_runtime"') || !queries[1].text.includes('ALTER ROLE "core_runtime" NOLOGIN') || !queries[2].text.includes("pg_terminate_backend(pid) AS terminated") || /password|scram/i.test(JSON.stringify(queries))) throw new Error("Runtime identity revocation did not use the bounded IAM-membership, no-login, and session-termination sequence.");
  await identityLifecycle.revokeRuntimeAccess({ query: async () => ({ rows: [] }) }, "core_runtime");
  await identityLifecycle.revokeRuntimeAccess({ query: async (statement) => ({ rows: statement.text.includes("pg_terminate_backend") ? [{ terminated: false }] : [] }) }, "core_runtime").then(() => { throw new Error("Runtime identity revocation accepted an unconfirmed termination."); }, () => undefined);
  const restored = [];
  let restoredLogin = false;
  await identityLifecycle.restoreRuntimeIamAccess({ query: async (statement) => { restored.push(statement); if (statement.text === 'ALTER ROLE "core_runtime" LOGIN') restoredLogin = true; return { rows: statement.text.startsWith("SELECT pg_has_role") ? [{ member: true }] : [{ exists: true, can_login: restoredLogin, superuser: false, create_role: false, create_database: false, replication: false, bypass_rls: false, inherit: false }] }; } }, "core_runtime");
  if (restored.length !== 5 || !restored[0].text.startsWith("SELECT EXISTS") || restored[0].values?.[0] !== "core_runtime" || restored[1].text !== 'ALTER ROLE "core_runtime" LOGIN' || !restored[2].text.startsWith("SELECT EXISTS") || !restored[3].text.includes('GRANT rds_iam TO "core_runtime"') || !restored[4].text.startsWith("SELECT pg_has_role") || /password|scram/i.test(JSON.stringify(restored))) throw new Error("Runtime identity restoration did not verify the bounded role before enabling login and restoring IAM membership.");
  const widened = [];
  await identityLifecycle.restoreRuntimeIamAccess({ query: async (statement) => { widened.push(statement); return { rows: [{ exists: true, can_login: false, superuser: false, create_role: false, create_database: true, replication: false, bypass_rls: false, inherit: false }] }; } }, "core_runtime").then(() => { throw new Error("Runtime identity restoration enabled a widened role."); }, () => undefined);
  if (widened.length !== 1 || !widened[0].text.startsWith("SELECT EXISTS")) throw new Error("Runtime identity restoration did not stop before enabling a widened role.");
}

async function captureConsole(run) {
  const originalLog = console.log, originalError = console.error, originalExitCode = process.exitCode;
  const records = [];
  console.log = (...values) => records.push(values.join(" "));
  console.error = (...values) => records.push(values.join(" "));
  process.exitCode = undefined;
  try { await run(); return { output: records.join("\n"), exitCode: process.exitCode ?? 0 }; }
  finally { console.log = originalLog; console.error = originalError; process.exitCode = originalExitCode; }
}

async function start(persistence) {
  const started = await serverMain.startPlatformServerProcess({
    apps: [program.createKanbienCoreServerPersistenceApp(releaseIdentity, persistence)],
    env: { HOST: "127.0.0.1", PORT: "3000", PLATFORM_SOURCE_COMMIT_SHA: releaseIdentity.sourceCommitSha },
    host: "127.0.0.1",
    port: 0,
    installSignalHandlers: false,
    logger: { write: () => undefined },
  });
  if (!started.ok) throw new Error(`Persistence composition did not start: ${started.error.code}`);
  return started.value;
}

function acceptanceRequest() {
  return { record_id: recordId, fact_digest: factDigest };
}

function fakePersistence({ readiness, create, read }) {
  return {
    closed: false,
    readiness: async () => readiness,
    createAcceptanceRecord: async () => create,
    readAcceptanceRecord: async () => read === "found" ? { outcome: "found", record: { id: recordId, factDigest } } : { outcome: read },
    deleteAcceptanceRecord: async () => "deleted",
    close: async function close() { this.closed = true; },
  };
}

function request(port, method, path, jsonBody) {
  return new Promise((resolve, reject) => {
    const body = jsonBody === undefined ? undefined : JSON.stringify(jsonBody);
    const requestHandle = httpRequest({
      host: "127.0.0.1",
      port,
      path,
      method,
      headers: body === undefined ? undefined : { "content-type": "application/json", "content-length": Buffer.byteLength(body) },
    }, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => { body += chunk; });
      response.on("end", () => resolve({ status: response.statusCode, body }));
    });
    requestHandle.on("error", reject);
    requestHandle.end(body);
  });
}

function assertStatus(response, expectedStatus, explanation) {
  if (response.status !== expectedStatus) {
    throw new Error(`${explanation}: expected ${expectedStatus}, received ${response.status}.`);
  }
}

function assertJson(response, expectedStatus, expectedBody, explanation) {
  assertStatus(response, expectedStatus, explanation);
  if (response.body !== JSON.stringify(expectedBody)) {
    throw new Error(`${explanation}: response body did not match the safe contract.`);
  }
}

function pathToFileUrl(path) {
  return new URL(`file://${path}`).href;
}
