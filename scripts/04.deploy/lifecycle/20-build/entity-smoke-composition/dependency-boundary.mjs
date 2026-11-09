// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.dependency-boundary
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Compare the isolated compiler source closure with reviewed program dependencies and reject forbidden or missing compiled owners.
//   portability: {class: internal, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.test.entity-smoke.composition.wrapper
//     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh

import assert from "node:assert/strict";
import { existsSync } from "node:fs";
import { resolve, relative, join } from "node:path";
import { builtinModules } from "node:module";
import { spawnSync } from "node:child_process";
import ts from "typescript";

const root = process.cwd();
const compiled = resolve(process.argv[2]);
const contract = spawnSync("python3", ["-c", "import json, pathlib, yaml; print(json.dumps(yaml.safe_load(pathlib.Path('infra/04.deploy/03.product/entrypoints/runnable-program-index.yml').read_text())))"], { encoding: "utf8" });
assert.equal(contract.status, 0, "the governed program contract must be readable");
const index = JSON.parse(contract.stdout);
const declaration = index.runnable_programs.find(item => item.id === "kanbien-entity-smoke");
assert(declaration, "the selected program must be registered");
const configuration = ts.readConfigFile("infra/04.deploy/03.product/entrypoints/kanbien-entity-smoke.tsconfig.json", ts.sys.readFile);
assert.equal(configuration.error, undefined);
const parsed = ts.parseJsonConfigFileContent(configuration.config, ts.sys, resolve("infra/04.deploy/03.product/entrypoints"));
assert.equal(parsed.errors.length, 0);
const program = ts.createProgram(parsed.fileNames, parsed.options);
const workspace = [
  ["platform/adapters/aws/persistence/postgresql/", "platform-adapter-aws-postgresql"],
  ["packages/core/", "core"],
  ["apps/entity-smoke/", "app-entity-smoke"],
  ...["config", "contracts", "health", "observability", "persistence", "runtime", "security", "server"].map(name => ["platform/" + name + "/", "platform-" + name]),
];
const borrowed = new Set([
  "kanbien-core-server-persistence-configuration.ts", "kanbien-core-server-persistence-composition.ts",
  "kanbien-core-server-persistence-postgresql.ts", "kanbien-core-server-persistence.app.ts",
  "kanbien-core-server-persistence-diagnostics.ts", "kanbien-core-server-persistence-role-credential.ts",
  "kanbien-core-server-persistence-operation-diagnostics.ts",
].map(name => "infra/04.deploy/03.product/entrypoints/" + name));
const ownSource = /^infra\/04\.deploy\/03\.product\/entrypoints\/(?:entity-smoke\/[^/]+\.ts|kanbien-entity-smoke(?:-migration|-administration|-verifier|-database-proof)?\.main\.ts)$/;
function ownerOf(source) {
  const found = workspace.find(([prefix]) => source.startsWith(prefix));
  if (found) return found[1];
  if (borrowed.has(source) || ownSource.test(source)) return "target-composition";
  assert.fail("a source outside the reviewed feature boundary is present");
}
const observed = new Set();
let sources = 0;
for (const source of program.getSourceFiles()) {
  if (source.isDeclarationFile || source.fileName.includes("/node_modules/")) continue;
  const name = relative(root, source.fileName);
  const owner = ownerOf(name);
  if (owner !== "target-composition") observed.add(owner);
  assert(existsSync(join(compiled, name.replace(/\.ts$/, ".js"))), "each actual source must be compiled in the selected payload");
  sources++;
  for (const imported of ts.preProcessFile(source.text, true, true).importedFiles) {
    const specifier = imported.fileName;
    if (specifier.startsWith(".") || specifier.startsWith("@kanbien/") || specifier.startsWith("node:") || builtinModules.includes(specifier)) continue;
    assert(["pg", "@aws-sdk/rds-signer"].includes(specifier), "an external dependency is outside the reviewed PostgreSQL selection");
    observed.add("postgresql");
  }
}
const dependencies = [...observed].sort();
assert.deepEqual(dependencies, [...declaration.observed_dependencies].sort(), "observed dependencies must be current, not copied approval");
assert(dependencies.every(item => declaration.approved_dependencies.includes(item)));
assert(dependencies.every(item => !declaration.forbidden_dependencies.includes(item)));
assert.throws(() => ownerOf("platform/workers/src/index.ts"));
assert.throws(() => ownerOf("platform/adapters/aws/observability/cloudwatch/src/index.ts"));
assert.throws(() => ownerOf("products/kanbien-platform/src/index.ts"));
console.log(JSON.stringify({ schema: "deploy/entity-smoke-dependency-observation/v1", verdict: "passed",
  program_id: "kanbien-entity-smoke", observed_dependencies: dependencies, source_file_count: sources,
  inputs: ["typescript-resolved-source-closure", "reviewed-program-declaration", "fresh-compiled-output"] }));

