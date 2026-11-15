// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.dependency-boundary
//   version: 3
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-15"
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
import { existsSync, readFileSync } from "node:fs";
import { resolve, relative, join } from "node:path";
import { builtinModules } from "node:module";
import ts from "typescript";
import { readProgramBuildInputs } from "../runnable-program-contract/build-inputs.mjs";

const root = process.cwd();
const compiled = resolve(process.argv[2]);
const declaration = readProgramBuildInputs(root, { programId: "kanbien-entity-smoke" });
const configuration = ts.readConfigFile(declaration.project, ts.sys.readFile);
assert.equal(configuration.error, undefined);
const parsed = ts.parseJsonConfigFileContent(configuration.config, ts.sys, resolve("infra/04.deploy/03.product/entrypoints"));
assert.equal(parsed.errors.length, 0);
const program = ts.createProgram([...new Set([...parsed.fileNames, ...declaration.inputs.sourceFiles.map(file => resolve(root, file))])],
  { ...parsed.options, baseUrl: root, paths: declaration.inputs.compilerPaths });
assert.equal(ts.getPreEmitDiagnostics(program).length, 0, "the observed program must resolve and typecheck, not silently omit failed imports");
const workspace = Object.entries(declaration.workspaceOwners).sort(([left], [right]) => right.length - left.length);
const borrowed = new Set([
  "shared/persistence/configuration.ts", "shared/persistence/role-credential.ts",
  "shared/persistence/operation-diagnostics.ts",
  "shared/persistence/configuration-implementation.ts",
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
    const packageName = specifier.startsWith("@") ? specifier.split("/").slice(0, 2).join("/") : specifier.split("/")[0];
    assert(Object.hasOwn(declaration.externalOwners, packageName), "an external dependency is outside the reviewed program selection");
    observed.add(declaration.externalOwners[packageName]);
  }
}
const dependencies = [...observed].sort();
assert.deepEqual(dependencies, [...declaration.observedDependencies].sort(), "observed dependencies must be current, not copied approval");
assert(dependencies.every(item => declaration.approvedDependencies.includes(item)));
assert(dependencies.every(item => !declaration.forbiddenDependencies.includes(item)));
assert.throws(() => ownerOf("platform/workers/src/index.ts"));
assert.throws(() => ownerOf("platform/adapters/aws/observability/cloudwatch/src/index.ts"));
assert.throws(() => ownerOf("products/kanbien-platform/src/index.ts"));
const imageRoot = "infra/04.deploy/03.product/image/entity-smoke/";
const dockerfile = readFileSync(imageRoot + "Dockerfile", "utf8");
const dockerignore = readFileSync(imageRoot + "Dockerfile.dockerignore", "utf8");
function assertBorrowedCopies(source, context) {
  const copies = new Set(source.split(/\r?\n/));
  const allowed = new Set(context.split(/\r?\n/));
  for (const file of borrowed) {
    assert(copies.has(`COPY ${file} ./${file}`), "each reviewed shared source must be copied into the feature build");
    assert(allowed.has("!" + file), "the default-deny build context must admit each copied shared source");
    const parts = file.split("/");
    for (let depth = 1; depth < parts.length; depth++) {
      assert(allowed.has("!" + parts.slice(0, depth).join("/") + "/"), "the copied shared source must have admitted parent directories");
    }
  }
}
assertBorrowedCopies(dockerfile, dockerignore);
for (const source of borrowed) {
  assert.throws(() => assertBorrowedCopies(dockerfile.replace(`COPY ${source} ./${source}`, ""), dockerignore));
}
for (const required of [...borrowed, "infra/04.deploy/03.product/entrypoints/shared/", "infra/04.deploy/03.product/entrypoints/shared/persistence/"]) {
  assert.throws(() => assertBorrowedCopies(dockerfile, dockerignore.split(/\r?\n/).filter(line => line !== "!" + required).join("\n")));
}
for (const name of ["kanbien-core-server-persistence-composition", "kanbien-core-server-persistence-postgresql", "kanbien-core-server-persistence.app", "kanbien-core-server-persistence-diagnostics", "kanbien-core-server-persistence-configuration", "kanbien-core-server-persistence-role-credential", "kanbien-core-server-persistence-operation-diagnostics"]) {
  const source = "infra/04.deploy/03.product/entrypoints/" + name;
  assert.throws(() => ownerOf(source + ".ts"), "configuration must not silently regain a dependency on the baseline application");
  assert.equal(existsSync(join(compiled, source + ".js")), false, "fresh feature output must not contain baseline application code");
  assert.equal(dockerfile.includes(`COPY ${source}.ts `), false);
  assert.equal(dockerignore.split(/\r?\n/).includes("!" + source + ".ts"), false);
}
console.log(JSON.stringify({ schema: "deploy/entity-smoke-dependency-observation/v1", verdict: "passed",
  program_id: "kanbien-entity-smoke", observed_dependencies: dependencies, source_file_count: sources,
  inputs: ["typescript-resolved-source-closure", "reviewed-program-declaration", "fresh-compiled-output"] }));

