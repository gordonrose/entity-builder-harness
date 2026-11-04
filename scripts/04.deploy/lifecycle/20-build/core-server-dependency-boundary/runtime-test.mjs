#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.core-server-program-runtime
//   version: 2
//   status: draft
//   created_on: "2026-10-19"
//   updated_on: "2026-10-30"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: script
//   purpose: Prove the compiled core server program serves only its safe release-verification operation through the generic server lifecycle.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.test.core-server-dependency-boundary
//     path: scripts/04.deploy/lifecycle/20-build/core-server-dependency-boundary/smoke-test.sh

import { deepEqual } from "node:assert/strict";
import { request as httpRequest } from "node:http";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";

const buildOutput = process.argv[2];
if (typeof buildOutput !== "string" || buildOutput.length === 0) {
  throw new Error("Usage: runtime-test.mjs <compiled-output-directory>");
}

const runtimeRoot = buildOutput;
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
    "./security": "packages/core/src/security/index.js",
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

const program = await import(pathToFileUrl(join(runtimeRoot, "infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.js")));
const serverMain = await import(pathToFileUrl(join(runtimeRoot, "platform/server/src/main.js")));
const releaseIdentity = { sourceCommitSha: "runtime-proof-2026.10.19" };
const startupLogs = [];
const started = await serverMain.startPlatformServerProcess({
  apps: [program.createKanbienCoreServerVerificationApp(releaseIdentity)],
  env: { HOST: "synthetic-private-listener.internal", PORT: "invalid-private-port", PLATFORM_SOURCE_COMMIT_SHA: releaseIdentity.sourceCommitSha },
  host: "127.0.0.1",
  port: 0,
  installSignalHandlers: false,
  logger: { write: (record) => startupLogs.push(record) },
});

if (!started.ok) {
  throw new Error(`Core server program did not start: ${started.error.code}`);
}

try {
  const configuration = startupLogs.filter((record) => record.message === "platform.diagnostic.observed"
    && record.fields?.capability === "platform-server" && record.fields?.operation === "configure" && record.fields?.stage === "configuration");
  const choiceCodes = new Set(["platform-server.listener-configuration-selected", "platform-server.port-configuration-fallback",
    "platform-server.health-exposure-selected", "platform-server.health-exposure-fallback"]);
  const choices = configuration.filter((record) => choiceCodes.has(record.fields.diagnostic.code));
  const diagnostic = (code, detail) => ({ schema: "core/diagnostic-record/v1", code, definitionVersion: 1, detail });
  deepEqual(choices.map((record) => record.fields.diagnostic), [
    diagnostic("platform-server.listener-configuration-selected", { phase: "configuration", setting: "http.host", source: "process-option", reason: "explicit-override", effect: "selected" }),
    diagnostic("platform-server.listener-configuration-selected", { phase: "configuration", setting: "http.port", source: "process-option", reason: "explicit-override", effect: "selected" }),
    diagnostic("platform-server.health-exposure-selected", { phase: "configuration", setting: "http.health.liveness-exposure", source: "default", exposure: "public", reason: "missing", effect: "default-selected" }),
    diagnostic("platform-server.health-exposure-selected", { phase: "configuration", setting: "http.health.readiness-exposure", source: "default", exposure: "public", reason: "missing", effect: "default-selected" }),
  ], "Compiled bootstrap retains the exact four listener/health choices independently of other configuration diagnostics.");
  deepEqual(configuration.filter((record) => record.fields.diagnostic.code === "platform-server.configuration-omitted").map((record) => record.fields.diagnostic), [
    diagnostic("platform-server.configuration-omitted", { phase: "configuration", setting: "http.cors-origin", reason: "missing", effect: "omitted" }),
    diagnostic("platform-server.configuration-omitted", { phase: "configuration", setting: "http.cors-allowlist", reason: "missing", effect: "omitted" }),
  ], "Absent CORS choices are omitted; the supplied valid release identity must not be reported as omitted.");
  if (JSON.stringify(startupLogs).includes("synthetic-private-listener.internal")
    || JSON.stringify(startupLogs).includes("invalid-private-port")) throw new Error("Compiled bootstrap must retain safe configuration choices and explicit option precedence.");
  const response = await localGet(started.value.handle.port, "/internal/release-verification");
  if (response.status !== 200 || response.body !== JSON.stringify({ release: releaseIdentity })) {
    throw new Error("Core server release-verification response did not match its safe identity contract.");
  }

  const missing = await localGet(started.value.handle.port, "/smoke/product");
  if (missing.status !== 404) {
    throw new Error("Core server unexpectedly mounted a product route.");
  }
} finally {
  await started.value.close();
}

console.log("Core server compiled runtime proof passed.");

function writePackageShim(packageName, exportsMap) {
  const packageRoot = join(runtimeRoot, "node_modules", ...packageName.split("/"));
  const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    const shimPath = exportName === "."
      ? join(packageRoot, "index.js")
      : join(packageRoot, exportName.slice(2), "index.js");
    mkdirSync(dirname(shimPath), { recursive: true });
    const target = join(runtimeRoot, targetPath);
    const modulePath = relative(dirname(shimPath), target).replaceAll("\\", "/");
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(modulePath.startsWith(".") ? modulePath : `./${modulePath}`)});\n`);
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }
  writeFileSync(
    join(packageRoot, "package.json"),
    `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`,
  );
}

function localGet(port, path) {
  return new Promise((resolve, reject) => {
    const request = httpRequest({ host: "127.0.0.1", port, path, method: "GET" }, (response) => {
      let body = "";
      response.setEncoding("utf8");
      response.on("data", (chunk) => {
        body += chunk;
      });
      response.on("end", () => resolve({ status: response.statusCode, body }));
    });
    request.on("error", reject);
    request.end();
  });
}

function pathToFileUrl(path) {
  return new URL(`file://${path}`).href;
}
