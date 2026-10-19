#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.command.build-core-server-image.prepare-runtime
//   version: 1
//   status: draft
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: script
//   purpose: Add only the generated CommonJS package shims required by the compiled Kanbien core-server payload.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.command.build-core-server-image
//     path: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh

import { mkdirSync, writeFileSync } from "node:fs";
import path, { join, relative } from "node:path";

const compiledRoot = parseCompiledRoot(process.argv.slice(2));
const coreModules = [
  "audit", "authn", "authz", "config", "diagnostics", "events", "i18n",
  "logging", "monitoring", "queues", "shared", "tenancy", "validation",
];
const packages = {
  "@kanbien/core": {
    ".": "packages/core/src/index.js",
    ...Object.fromEntries(coreModules.map((moduleName) => [`./${moduleName}`, `packages/core/src/${moduleName}/index.js`])),
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
writeFileSync(
  join(compiledRoot, "kanbien-core-server.main.js"),
  'require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.js");\n',
);

function parseCompiledRoot(args) {
  if (args.length !== 2 || args[0] !== "--compiled-root" || args[1].length === 0) {
    throw new Error("Usage: prepare-runtime.mjs --compiled-root <compiled-output-directory>");
  }
  return args[1];
}

function writePackageShim(packageName, exportsMap) {
  const packageRoot = join(compiledRoot, "node_modules", ...packageName.split("/"));
  const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    const shimPath = exportName === "." ? join(packageRoot, "index.js") : join(packageRoot, exportName.slice(2), "index.js");
    mkdirSync(path.dirname(shimPath), { recursive: true });
    const target = join(compiledRoot, targetPath);
    const targetFromShim = relative(path.dirname(shimPath), target).replaceAll(path.sep, "/");
    const requirePath = targetFromShim.startsWith(".") ? targetFromShim : `./${targetFromShim}`;
    writeFileSync(shimPath, `module.exports = require(${JSON.stringify(requirePath)});\n`);
    packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }
  writeFileSync(join(packageRoot, "package.json"), `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`);
}
