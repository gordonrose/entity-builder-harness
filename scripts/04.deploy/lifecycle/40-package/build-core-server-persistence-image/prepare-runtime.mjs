#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.command.build-core-server-persistence-image.prepare-runtime
//   version: 1
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-10-23"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Add CommonJS workspace shims and executable wrappers to the persistence candidate payload.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import path, { join, relative } from "node:path";
const compiledRoot = parseCompiledRoot(process.argv.slice(2));
for (const entrypoint of [
  "kanbien-core-server-persistence.main.js",
  "kanbien-core-server-persistence-verifier.main.js",
  "kanbien-core-server-persistence-migration.main.js",
  "kanbien-core-server-persistence-administration.main.js",
  "kanbien-core-server-persistence-restore-verifier.main.js",
]) {
  const compiledEntrypoint = join(compiledRoot, "infra/04.deploy/03.product/entrypoints", entrypoint);
  if (!existsSync(compiledEntrypoint)) throw new Error(`Required compiled entrypoint is missing: ${entrypoint}`);
}
const coreModules = ["audit", "authn", "authz", "config", "diagnostics", "events", "i18n", "logging", "monitoring", "persistence", "queues", "shared", "tenancy", "validation"];
const packages = {
  "@kanbien/core": { ".": "packages/core/src/index.js", ...Object.fromEntries(coreModules.map((name) => [`./${name}`, `packages/core/src/${name}/index.js`])) },
  "@kanbien/platform-adapter-aws-persistence-postgresql": { ".": "platform/adapters/aws/persistence/postgresql/src/index.js" },
  "@kanbien/platform-adapter-aws-observability-cloudwatch": { ".": "platform/adapters/aws/observability/cloudwatch/src/index.js" },
  "@kanbien/platform-config": { ".": "platform/config/src/index.js" },
  "@kanbien/platform-contracts": { ".": "platform/contracts/src/index.js" },
  "@kanbien/platform-health": { ".": "platform/health/src/index.js" },
  "@kanbien/platform-observability": { ".": "platform/observability/src/index.js" },
  "@kanbien/platform-persistence": { ".": "platform/persistence/src/index.js" },
  "@kanbien/platform-runtime": { ".": "platform/runtime/src/index.js" },
  "@kanbien/platform-security": { ".": "platform/security/src/index.js" },
  "@kanbien/platform-server": { ".": "platform/server/src/index.js", "./main": "platform/server/src/main.js" },
};
for (const [name, exportsMap] of Object.entries(packages)) writePackageShim(name, exportsMap);
writeFileSync(join(compiledRoot, "kanbien-core-server-persistence.main.js"), [
  'const { runKanbienCoreServerPersistenceMain } = require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence.main.js");',
  "void runKanbienCoreServerPersistenceMain().catch(() => { process.exitCode = 1; });", "",
].join("\n"));
writeFileSync(join(compiledRoot, "kanbien-core-server-persistence-verifier.main.js"), [
  'const { runKanbienCoreServerPersistenceVerifier } = require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-verifier.main.js");',
  "void runKanbienCoreServerPersistenceVerifier().catch(() => { process.exitCode = 1; });", "",
].join("\n"));
writeFileSync(join(compiledRoot, "kanbien-core-server-persistence-migration.main.js"), [
  'const { runKanbienCoreServerPersistenceMigration } = require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-migration.main.js");',
  "void runKanbienCoreServerPersistenceMigration().catch(() => { process.exitCode = 1; });", "",
].join("\n"));
writeFileSync(join(compiledRoot, "kanbien-core-server-persistence-administration.main.js"), [
  'const { runKanbienCoreServerPersistenceAdministration } = require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-administration.main.js");',
  "void runKanbienCoreServerPersistenceAdministration().catch(() => { process.exitCode = 1; });", "",
].join("\n"));
writeFileSync(join(compiledRoot, "kanbien-core-server-persistence-restore-verifier.main.js"), [
  'const { runKanbienCoreServerPersistenceRestoreVerifier } = require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-restore-verifier.main.js");',
  "void runKanbienCoreServerPersistenceRestoreVerifier();",
].join("\n"));
function parseCompiledRoot(args) { if (args.length !== 2 || args[0] !== "--compiled-root" || args[1].length === 0) throw new Error("Usage: prepare-runtime.mjs --compiled-root <compiled-output-directory>"); return args[1]; }
function writePackageShim(packageName, exportsMap) {
  const packageRoot = join(compiledRoot, "node_modules", ...packageName.split("/")); const packageExports = {};
  for (const [exportName, targetPath] of Object.entries(exportsMap)) {
    const shimPath = exportName === "." ? join(packageRoot, "index.js") : join(packageRoot, exportName.slice(2), "index.js"); mkdirSync(path.dirname(shimPath), { recursive: true });
    const fromShim = relative(path.dirname(shimPath), join(compiledRoot, targetPath)).replaceAll(path.sep, "/"); writeFileSync(shimPath, `module.exports = require(${JSON.stringify(fromShim.startsWith(".") ? fromShim : `./${fromShim}`)});\n`); packageExports[exportName] = exportName === "." ? "./index.js" : `./${exportName.slice(2)}/index.js`;
  }
  writeFileSync(join(packageRoot, "package.json"), `${JSON.stringify({ name: packageName, type: "commonjs", exports: packageExports }, null, 2)}\n`);
}
