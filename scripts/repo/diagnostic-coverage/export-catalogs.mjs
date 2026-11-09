#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.diagnostics.export-catalogs
//   version: 4
//   status: active
//   created_on: "2026-10-27"
//   updated_on: "2026-11-09"
//   layer: 06.shared
//   domain: diagnostics
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Export reviewed executable diagnostic definitions for cross-language consumers without maintaining duplicate vocabularies.
//   portability: { class: source-only, targets: [] }
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.diagnostics.coverage
//     path: scripts/repo/diagnostic-coverage/script.sh
import { createRequire } from "node:module";
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import { catalogCompatible } from "./compatibility.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const args = process.argv.slice(2);
if (args[0] !== "--compiled-root" || !args[1] || args.slice(2).some((arg) => arg !== "--check")) throw new Error("Usage: export-catalogs.mjs --compiled-root <compiled-output> [--check]");
const compiled = resolve(args[1]);
// Resolve only the reviewed compiled workspace modules, never TypeScript or provider operations.
const packageSources = {
  "@kanbien/core": "packages/core/src/index.js",
  "@kanbien/app-entity-smoke": "apps/entity-smoke/src/index.js",
  "@kanbien/app-platform-smoke": "apps/platform-smoke/src/index.js",
  "@kanbien/product-kanbien-platform": "products/kanbien-platform/src/index.js",
  "@kanbien/platform-config": "platform/config/src/index.js",
  "@kanbien/platform-security": "platform/security/src/index.js",
  "@kanbien/platform-contracts": "platform/contracts/src/index.js",
  "@kanbien/platform-observability": "platform/observability/src/index.js",
  "@kanbien/platform-health": "platform/health/src/index.js",
  "@kanbien/platform-runtime": "platform/runtime/src/index.js",
  "@kanbien/platform-workers": "platform/workers/src/index.js",
  "@kanbien/platform-server": "platform/server/src/index.js",
  "@kanbien/platform-persistence": "platform/persistence/src/index.js",
  "@kanbien/platform-adapter-aws-persistence-postgresql": "platform/adapters/aws/persistence/postgresql/src/index.js",
  "@kanbien/platform-adapter-aws-queue-sqs": "platform/adapters/aws/queue/sqs/src/index.js",
};
const assetExports = [];
for (const [name, source] of Object.entries(packageSources)) {
  const directory = join(compiled, "node_modules", ...name.split("/"));
  mkdirSync(directory, { recursive: true });
  const exports = { ".": "./index.cjs" };
  writeFileSync(join(directory, "index.cjs"), `module.exports = require(${JSON.stringify(join(compiled, source))});\n`);
  if (name === "@kanbien/core") {
    const manifest = JSON.parse(readFileSync(join(root, "packages/core/package.json"), "utf8"));
    for (const [key, path] of Object.entries(manifest.exports)) {
      if (key === ".") continue;
      if (path.endsWith(".json")) {
        const output = join(directory, key.slice(2));
        exports[key] = `./${key.slice(2)}`;
        assetExports.push({ source: join(root, "packages/core", path), output });
        continue;
      }
      const filename = `${key.slice(2)}.cjs`;
      exports[key] = `./${filename}`;
      mkdirSync(dirname(join(directory, filename)), { recursive: true });
      writeFileSync(join(directory, filename), `module.exports = require(${JSON.stringify(join(compiled, "packages/core", path.replace(/\.ts$/, ".js")))});\n`);
    }
  }
  if (name === "@kanbien/platform-persistence" || name === "@kanbien/platform-adapter-aws-queue-sqs" || name === "@kanbien/platform-security" || name === "@kanbien/platform-workers") {
    const packageDirectory = name === "@kanbien/platform-persistence" ? "platform/persistence" : name === "@kanbien/platform-security" ? "platform/security" : name === "@kanbien/platform-workers" ? "platform/workers" : "platform/adapters/aws/queue/sqs";
    const manifest = JSON.parse(readFileSync(join(root, packageDirectory, "package.json"), "utf8"));
    for (const [key, target] of Object.entries(manifest.exports)) {
      if (!target.endsWith(".json")) continue;
      exports[key] = `./${key.slice(2)}`;
      assetExports.push({ source: join(root, packageDirectory, target), output: join(directory, key.slice(2)) });
    }
  }
  writeFileSync(join(directory, "package.json"), JSON.stringify({ name, type: "commonjs", exports }));
}
const require = createRequire(join(compiled, "diagnostic-export.cjs"));
const { diagnosticRelatedRecordLimit, validDiagnosticDefinition } = require(join(compiled, "packages/core/src/diagnostics/index.js"));
const selections = [
  ["platform/persistence/src/leasing", "platform/persistence/src/leasing/index.js", "persistenceLeasingDiagnosticCatalog", "diagnostics.v1.json", undefined, "contract/reporting"],
  ["platform/workers/src/configuration", "platform/workers/src/configuration/index.js", "workerRetryConfigurationDiagnosticCatalog", "diagnostics.v1.json", undefined, "contract/reporting"],
  ["packages/core", "packages/core/src/diagnostic-catalog.js", "coreDiagnosticCatalog"],
  ["packages/core/src/config", "packages/core/src/config/index.js", "coreConfigDiagnosticCatalog", "diagnostics.v1.json", undefined, "contract/reporting"],
  ["platform/contracts", "platform/contracts/src/registration-diagnostics.js", "platformContractDiagnosticCatalog"],
  ["platform/config", "platform/config/src/diagnostics.js", "platformConfigDiagnosticCatalog"],
  ["platform/observability", "platform/observability/src/configuration.js", "platformObservabilityDiagnosticCatalog"],
  ["platform/health", "platform/health/src/diagnostics.js", "platformHealthDiagnosticCatalog"],
  ["platform/runtime", "platform/runtime/src/diagnostics.js", "platformRuntimeDiagnosticCatalog"],
  ["platform/security", "platform/security/src/diagnostics.js", "platformSecurityDiagnosticCatalog"],
  ["platform/security/src/jwt-configuration", "platform/security/src/jwt-configuration/index.js", "jwtConfigurationDiagnosticCatalog", "diagnostics.v1.json", undefined, "contract/reporting"],
  ["platform/server", "platform/server/src/diagnostics.js", "platformServerDiagnosticCatalog"],
  ["platform/workers", "platform/workers/src/diagnostics.js", "platformWorkerDiagnosticCatalog"],
  ["platform/persistence", "platform/persistence/src/diagnostics.js", "platformPersistenceDiagnosticCatalog"],
  ["platform/persistence/src/maintenance", "platform/persistence/src/maintenance/index.js", "persistenceMaintenanceDiagnosticCatalog", "diagnostics.v1.json", undefined, "contract/reporting"],
  ["platform/adapters/aws/queue/sqs/src/configuration", "platform/adapters/aws/queue/sqs/src/configuration/index.js", "sqsConfigurationDiagnosticCatalog", "diagnostics.v1.json", undefined, "contract/reporting"],
  ["apps/platform-smoke", "apps/platform-smoke/src/diagnostics.js", "platformSmokeDiagnosticCatalog"],
  ["apps/entity-smoke", "apps/entity-smoke/features/test-entity/contract/diagnostics.js", "testEntityDiagnosticCatalog"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js", "entitySmokeTargetDiagnosticCatalog", "entity-smoke-target-diagnostics.v1.json"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-configuration.js", "persistenceTaskConfigurationDiagnosticCatalog"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-operation-diagnostics.js", "persistenceTaskOperationDiagnosticCatalog", "kanbien-core-server-persistence-operation-diagnostics.v1.json", "persistenceTaskFailureContract"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/kanbien-platform-postgresql-operation-diagnostics.js", "kanbienPlatformPostgreSqlOperationDiagnosticCatalog", "kanbien-platform-postgresql-operation-diagnostics.v1.json"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/kanbien-platform-configuration-diagnostics.js", "kanbienPlatformConfigurationDiagnosticCatalog", "kanbien-platform-diagnostics.v1.json"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/kanbien-core-server-persistence-diagnostics.js", "kanbienCoreAcceptanceDiagnosticCatalog", "kanbien-core-server-acceptance-diagnostics.v1.json"],
  ["infra/04.deploy/03.product/entrypoints", "infra/04.deploy/03.product/entrypoints/kanbien-platform-delivery-diagnostics.js", "kanbienPlatformDeliveryDiagnosticCatalog", "kanbien-platform-delivery-diagnostics.v1.json"],
];
let failed = false;
let incompatible = false;
const outputs = [];
execFileSync("git", ["-C", root, "rev-parse", "--verify", "HEAD"], { stdio: ["ignore", "pipe", "ignore"] });
for (const [owner, source, exported, filename = "diagnostics.v1.json", taskFailureExport, outputDirectory = "contracts"] of selections) {
  const selected = require(join(compiled, source));
  const catalog = selected[exported];
  const identities = new Set();
  if (!catalog || typeof catalog.owner !== "string" || !Array.isArray(catalog.definitions)
    || catalog.definitions.some((definition) => {
      if (!validDiagnosticDefinition(definition)) return true;
      const identity = `${definition.code}@${definition.version}`;
      if (identities.has(identity)) return true;
      identities.add(identity);
      return false;
    })) { incompatible = true; continue; }
  const content = JSON.stringify({ schema: "core/diagnostic-catalog-export/v1", delivery: { maxRelatedRecords: diagnosticRelatedRecordLimit,
    ...(taskFailureExport === undefined ? {} : { taskFailure: selected[taskFailureExport] }) }, catalog }, null, 2) + "\n";
  const output = join(root, owner, outputDirectory, filename);
  const relative = `${owner}/${outputDirectory}/${filename}`;
  let previous;
  try { previous = execFileSync("git", ["-C", root, "show", `HEAD:${relative}`], { stdio: ["ignore", "pipe", "ignore"] }).toString(); } catch { /* No committed export exists during first adoption. */ }
  if (previous !== undefined && !catalogCompatible(JSON.parse(previous), JSON.parse(content))) incompatible = true;
  outputs.push({ output, content });
  if (args.includes("--check")) {
    try { if (readFileSync(output, "utf8") !== content) failed = true; } catch { failed = true; }
  }
}
if (!args.includes("--check") && !incompatible) for (const { output, content } of outputs) {
  mkdirSync(dirname(output), { recursive: true });
  writeFileSync(output, content);
}
if (!failed && !incompatible) for (const { source, output } of assetExports) {
  mkdirSync(dirname(output), { recursive: true });
  copyFileSync(source, output);
}
console.log(JSON.stringify({ schema: "repo/diagnostic-export-report/v1", verdict: failed || incompatible ? "failed" : "passed", code: incompatible ? "diagnostic-definition-version-conflict" : failed ? "diagnostic-contract-export-stale" : "diagnostic-contract-exports-current" }));
if (failed || incompatible) process.exitCode = 1;
