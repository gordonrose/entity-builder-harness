#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.build-platform-shell-image.prepare-runtime
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - agentic
//   - sre
//   kind: script
//   purpose: Prepare CommonJS package shims for the platform shell image runtime payload.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.script.build-platform-shell-image
//     path: scripts/04.deploy/build-platform-shell-image/script.sh

import { mkdirSync, writeFileSync } from "node:fs";
import path, { join } from "node:path";

const runtimeRoot = ".cache/platform-shell-image-build";
const coreModules = [
  "audit",
  "authn",
  "authz",
  "config",
  "diagnostics",
  "events",
  "i18n",
  "logging",
  "monitoring",
  "queues",
  "shared",
  "tenancy",
  "validation",
];

writePackageShim("@kanbien/core", {
  ".": join(runtimeRoot, "packages/core/src/index.js"),
  ...Object.fromEntries(coreModules.map((moduleName) => [`./${moduleName}`, join(runtimeRoot, `packages/core/src/${moduleName}/index.js`)])),
});
writePackageShim("@kanbien/platform-contracts", {
  ".": join(runtimeRoot, "platform/contracts/src/index.js"),
});
writePackageShim("@kanbien/platform-config", {
  ".": join(runtimeRoot, "platform/config/src/index.js"),
});
writePackageShim("@kanbien/platform-health", {
  ".": join(runtimeRoot, "platform/health/src/index.js"),
});
writePackageShim("@kanbien/platform-observability", {
  ".": join(runtimeRoot, "platform/observability/src/index.js"),
});
writePackageShim("@kanbien/platform-runtime", {
  ".": join(runtimeRoot, "platform/runtime/src/index.js"),
});
writePackageShim("@kanbien/platform-security", {
  ".": join(runtimeRoot, "platform/security/src/index.js"),
});
writePackageShim("@kanbien/platform-server", {
  ".": join(runtimeRoot, "platform/server/src/index.js"),
  "./main": join(runtimeRoot, "platform/server/src/main.js"),
});

console.log(`Prepared platform shell image runtime at ${runtimeRoot}`);

function writePackageShim(packageName, exportsMap) {
  const packageRoot = join(runtimeRoot, "node_modules", ...packageName.split("/"));
  mkdirSync(packageRoot, { recursive: true });

  const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    const shimPath = exportName === "."
      ? join(packageRoot, "index.js")
      : join(packageRoot, exportName.slice(2), "index.js");
    mkdirSync(path.dirname(shimPath), { recursive: true });
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(relativeRequirePath(shimPath, targetPath))});\n`);
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }

  writeFileSync(
    join(packageRoot, "package.json"),
    `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`,
  );
}

function relativeRequirePath(fromFile, toFile) {
  const relativePath = path.relative(path.dirname(fromFile), toFile).replaceAll(path.sep, "/");
  return relativePath.startsWith(".") ? relativePath : `./${relativePath}`;
}
