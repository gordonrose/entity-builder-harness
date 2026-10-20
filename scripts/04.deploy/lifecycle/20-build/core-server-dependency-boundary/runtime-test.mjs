#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.test.core-server-program-runtime
//   version: 1
//   status: draft
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
const started = await serverMain.startPlatformServerProcess({
  apps: [program.createKanbienCoreServerVerificationApp(releaseIdentity)],
  env: { HOST: "127.0.0.1", PORT: "3000", PLATFORM_SOURCE_COMMIT_SHA: releaseIdentity.sourceCommitSha },
  host: "127.0.0.1",
  port: 0,
  installSignalHandlers: false,
  logger: { write: () => undefined },
});

if (!started.ok) {
  throw new Error(`Core server program did not start: ${started.error.code}`);
}

try {
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
