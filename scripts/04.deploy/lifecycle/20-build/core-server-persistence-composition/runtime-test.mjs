#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-composition-runtime
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-24"
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
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const buildOutput = process.argv[2];
if (typeof buildOutput !== "string" || buildOutput.length === 0) {
  throw new Error("Usage: runtime-test.mjs <compiled-output-directory>");
}

const packages = {
  "@kanbien/core": {
    ".": "packages/core/src/index.js",
    "./audit": "packages/core/src/audit/index.js",
    "./authn": "packages/core/src/authn/index.js",
    "./authz": "packages/core/src/authz/index.js",
    "./config": "packages/core/src/config/index.js",
    "./diagnostics": "packages/core/src/diagnostics/index.js",
    "./events": "packages/core/src/events/index.js",
    "./i18n": "packages/core/src/i18n/index.js",
    "./logging": "packages/core/src/logging/index.js",
    "./monitoring": "packages/core/src/monitoring/index.js",
    "./queues": "packages/core/src/queues/index.js",
    "./shared": "packages/core/src/shared/index.js",
    "./tenancy": "packages/core/src/tenancy/index.js",
    "./validation": "packages/core/src/validation/index.js",
  },
  "@kanbien/platform-config": { ".": "platform/config/src/index.js" },
  "@kanbien/platform-contracts": { ".": "platform/contracts/src/index.js" },
  "@kanbien/platform-health": { ".": "platform/health/src/index.js" },
  "@kanbien/platform-observability": { ".": "platform/observability/src/index.js" },
  "@kanbien/platform-runtime": { ".": "platform/runtime/src/index.js" },
  "@kanbien/platform-security": { ".": "platform/security/src/index.js" },
  "@kanbien/platform-server": {
    ".": "platform/server/src/index.js",
    "./main": "platform/server/src/main.js",
  },
};

for (const [packageName, exportsMap] of Object.entries(packages)) {
  writePackageShim(packageName, exportsMap);
}

const program = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.app.js")));
const serverMain = await import(pathToFileUrl(join(buildOutput, "platform/server/src/main.js")));
const verifier = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.js")));
const migration = await import(pathToFileUrl(join(buildOutput, "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-runtime-credential.js")));
const releaseIdentity = { sourceCommitSha: "local-persistence-composition-proof-2026.10.23" };
const recordId = "core-persistence-acceptance-0001";
const factDigest = "a".repeat(64);

await proveUnavailableDependency();
await proveAvailableDependency();
await proveHealthVerifierModes();
await proveRuntimeCredentialRevocationOperation();

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

async function proveRuntimeCredentialRevocationOperation() {
  if (migration.runtimeCredentialOperation(undefined) !== "apply" || migration.runtimeCredentialOperation("rotate") !== "rotate" || migration.runtimeCredentialOperation("revoke") !== "revoke" || migration.runtimeCredentialOperation("prove-effective-privilege") !== "prove-effective-privilege" || migration.runtimeCredentialOperation("unsafe") !== undefined) throw new Error("Migration credential operation parsing is not fail-closed.");
  const queries = [];
  await migration.revokeRuntimeAccess({ query: async (statement) => { queries.push(statement); return { rows: statement.text.includes("pg_terminate_backend") ? [{ terminated: true }] : [] }; } }, "core_runtime");
  if (queries.length !== 2 || !queries[0].text.includes('ALTER ROLE "core_runtime" NOLOGIN') || !queries[1].text.includes("pg_terminate_backend") || JSON.stringify(queries).includes("password")) throw new Error("Runtime credential revocation did not use the bounded no-login and session-termination sequence.");
  await migration.revokeRuntimeAccess({ query: async (statement) => ({ rows: statement.text.includes("pg_terminate_backend") ? [{ terminated: false }] : [] }) }, "core_runtime").then(() => { throw new Error("Runtime credential revocation accepted an unconfirmed termination."); }, () => undefined);
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

function writePackageShim(packageName, exportsMap) {
  const packageRoot = join(buildOutput, "node_modules", ...packageName.split("/"));
  const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    const shimPath = exportName === "." ? join(packageRoot, "index.js") : join(packageRoot, exportName.slice(2), "index.js");
    mkdirSync(dirname(shimPath), { recursive: true });
    const target = join(buildOutput, targetPath);
    const modulePath = relative(dirname(shimPath), target).replaceAll("\\\\", "/");
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(modulePath.startsWith(".") ? modulePath : `./${modulePath}`)});\n`);
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }
  writeFileSync(join(packageRoot, "package.json"), `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`);
}

function pathToFileUrl(path) {
  return new URL(`file://${path}`).href;
}
