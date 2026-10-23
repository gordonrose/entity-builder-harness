#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-persistence-composition-runtime
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
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
const releaseIdentity = { sourceCommitSha: "local-persistence-composition-proof-2026.10.23" };

await proveUnavailableDependency();
await proveAvailableDependency();

console.log("Core-server persistence composition local runtime proof passed.");

async function proveUnavailableDependency() {
  const fake = fakePersistence({ readiness: "not-ready", create: "unavailable", read: "unavailable" });
  const started = await start(fake);
  try {
    assertStatus(await request(started.handle.port, "GET", "/livez"), 200, "liveness must remain live while persistence is unavailable");
    assertStatus(await request(started.handle.port, "GET", "/readyz"), 503, "readiness must report the unavailable persistence dependency");
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance"), 503, { outcome: "not-confirmed" }, "unavailable persistence must return only a controlled outcome");
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
    assertJson(await request(started.handle.port, "POST", "/internal/persistence-acceptance"), 201, { outcome: "created" }, "server-mediated acceptance create must expose a stable result");
    assertJson(await request(started.handle.port, "GET", "/internal/persistence-acceptance"), 200, { outcome: "found", release: releaseIdentity }, "server-mediated acceptance read must expose only a stable result and release identity");
    assertStatus(await request(started.handle.port, "GET", "/smoke/product"), 404, "composition must not mount product functionality");
  } finally {
    await started.close();
  }
  if (!fake.closed) throw new Error("Core-server shutdown did not close the injected persistence runtime.");
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

function fakePersistence({ readiness, create, read }) {
  return {
    closed: false,
    readiness: async () => readiness,
    createAcceptanceRecord: async () => create,
    readAcceptanceRecord: async () => read,
    close: async function close() { this.closed = true; },
  };
}

function request(port, method, path) {
  return new Promise((resolve, reject) => {
    const requestHandle = httpRequest({ host: "127.0.0.1", port, path, method }, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => { body += chunk; });
      response.on("end", () => resolve({ status: response.statusCode, body }));
    });
    requestHandle.on("error", reject);
    requestHandle.end();
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
