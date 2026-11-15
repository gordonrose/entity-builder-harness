// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.prepare-runtime-payload
//   version: 1
//   status: draft
//   created_on: "2026-11-14"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove both real payload adapters, Docker script closures and renamed mappings without compiling, Docker or AWS.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.prepare-runtime-payload.wrapper
//     path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/script.sh

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { assembleRuntimePayload } from "./assemble.mjs";
import { loadWorkspaceGraph } from "../../../../repo/workspace-build/declarations.mjs";

const root = fileURLToPath(new URL("../../../../../", import.meta.url));
const home = "scripts/04.deploy/lifecycle/40-package";
const sharedAssembler = `${home}/prepare-runtime-payload/assemble.mjs`;
const sharedBuild = "scripts/repo/workspace-build";
const programReader = "scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs";
const programIndex = "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml";
const contextRequirements = new Map([
  [sharedAssembler, [`!${home}/prepare-runtime-payload/`, `!${sharedAssembler}`]],
  ...["runtime-packages.mjs", "declarations.mjs"].map(name => [`${sharedBuild}/${name}`,
    ["!scripts/repo/", `!${sharedBuild}/`, `!${sharedBuild}/${name}`]]),
  [programReader, ["!scripts/04.deploy/lifecycle/20-build/", "!scripts/04.deploy/lifecycle/20-build/runnable-program-contract/", "!" + programReader]],
  [programIndex, ["!" + programIndex]],
]);
const contextExceptions = [...new Set([...contextRequirements.values()].flat())];
const entriesHome = "infra/04.deploy/03.product/entrypoints";
const canary = "PRIVATE_PAYLOAD_PATH_CANARY";
const coreExports = JSON.parse(readFileSync(join(root, "packages/core/package.json"))).exports;
const workspaceGraph = loadWorkspaceGraph(root);
const entries = {
  "core-server-persistence": {
    "kanbien-core-server-persistence.main": ["runKanbienCoreServerPersistenceMain"],
    "kanbien-core-server-persistence-verifier.main": ["runKanbienCoreServerPersistenceVerifier"],
    "kanbien-core-server-persistence-migration.main": ["runKanbienCoreServerPersistenceMigration"],
    "kanbien-core-server-persistence-administration.main": ["runKanbienCoreServerPersistenceAdministration"],
    "kanbien-core-server-persistence-restore-verifier.main": ["runKanbienCoreServerPersistenceRestoreVerifier"],
  },
  "entity-smoke": {
    "kanbien-entity-smoke.main": ["runEntitySmokeMain", "startup"],
    "kanbien-entity-smoke-migration.main": ["runEntitySmokeMigration", "migration"],
    "kanbien-entity-smoke-administration.main": ["runEntitySmokeAdministration", "administration"],
    "kanbien-entity-smoke-verifier.main": ["runEntitySmokeVerifier", "verification"],
    "kanbien-entity-smoke-database-proof.main": ["runEntitySmokeDatabaseProof", "verification"],
  },
};
function put(file, text) { mkdirSync(dirname(file), { recursive: true }); writeFileSync(file, text); }
function run(file, args = [], cwd = root) { return spawnSync(process.execPath, [file, ...args], { cwd, encoding: "utf8", timeout: 15000, env: { ...process.env, NODE_PATH: "" } }); }
function snapshot(directory) {
  return Object.fromEntries(readdirSync(directory, { recursive: true, withFileTypes: true }).filter(entry => entry.isFile()).map(entry => {
    const file = join(entry.parentPath ?? entry.path, entry.name);
    return [file.slice(directory.length + 1), readFileSync(file).toString("base64")];
  }).sort(([a], [b]) => a.localeCompare(b)));
}
function fixture(kind, body, omittedContextException) {
  const temporary = mkdtempSync(join(tmpdir(), "runtime-payload-")), repository = join(temporary, "repository"), compiled = join(temporary, canary);
  try {
    const dockerfile = readFileSync(join(root, `infra/04.deploy/03.product/image/${kind}/Dockerfile`), "utf8");
    const context = readFileSync(join(root, `infra/04.deploy/03.product/image/${kind}/Dockerfile.dockerignore`), "utf8")
      .split(/\r?\n/).filter(line => line !== omittedContextException);
    assert(context.includes("*"), "fixture models the existing default-deny build context");
    // Model only the shared files' explicit parent/file exceptions, not arbitrary
    // Dockerignore patterns. The unchanged script contexts remain source-owned.
    // Materialise actual Docker COPY script declarations. An omitted transitive
    // import fails the actual CLI, not a matching-string assertion.
    for (const [, source, target] of dockerfile.matchAll(/^COPY ((?:scripts\/\S+\.mjs)|(?:infra\/\S+\/runnable-program-index\.yml)) \.\/(\S+)$/gm)) {
      if (contextRequirements.has(source) && !contextRequirements.get(source).every(line => context.includes(line))) continue;
      put(join(repository, target), readFileSync(join(root, source)));
    }
    put(join(repository, "package.json"), readFileSync(join(root, "package.json")));
    cpSync(join(root, "node_modules/yaml"), join(repository, "node_modules/yaml"), { recursive: true });
    const feature = kind === "entity-smoke";
    const core = coreExports;
    const packages = { "@kanbien/core": Object.fromEntries(Object.entries(core).map(([key, value]) => [key, "packages/core/" + value.slice(2).replace(/\.ts$/, ".js")])) };
    const platform = ["config", "contracts", "health", "observability", "persistence", "runtime", "security"];
    if (feature) packages["@kanbien/app-entity-smoke"] = { ".": "apps/entity-smoke/src/index.js" };
    else packages["@kanbien/platform-adapter-aws-observability-cloudwatch"] = { ".": "platform/adapters/aws/observability/cloudwatch/src/index.js" };
    if (!feature) packages["@kanbien/platform-adapter-aws-persistence-postgresql"] = { ".": "platform/adapters/aws/persistence/postgresql/src/index.js" };
    for (const name of platform) packages["@kanbien/platform-" + name] = { ".": "platform/" + name + "/src/index.js" };
    packages["@kanbien/platform-server"] = { ".": "platform/server/src/index.js", "./main": "platform/server/src/main.js" };
    if (feature) packages["@kanbien/platform-adapter-aws-persistence-postgresql"] = { ".": "platform/adapters/aws/persistence/postgresql/src/index.js" };
    // Expected membership stays independently explicit above. Public export
    // details come from each package declaration, as required for new exports.
    for (const name of Object.keys(packages)) {
      const owner = workspaceGraph.packages.get(name);
      put(join(repository, owner.manifestPath), readFileSync(join(root, owner.manifestPath)));
      packages[name] = Object.fromEntries(Object.keys(owner.manifest.exports).sort().map(key => {
        const source = owner.directory + "/" + owner.manifest.exports[key].slice(2);
        put(join(repository, source), readFileSync(join(root, source)));
        return [key, source.replace(/\.ts$/, ".js")];
      }));
    }
    const orderedPackages = Object.fromEntries(Object.keys(packages).sort().map(name => [name, packages[name]]));
    const project = `${entriesHome}/kanbien-${feature ? "entity-smoke" : "core-server-persistence"}.tsconfig.json`;
    put(join(repository, project), readFileSync(join(root, project)));
    for (const targets of Object.values(packages)) for (const target of Object.values(targets)) {
      if (target.endsWith(".json")) put(join(repository, target), readFileSync(join(root, target)));
      else put(join(compiled, target), "module.exports = { marker: " + JSON.stringify(target) + " };\n");
    }
    for (const [entry, [exported]] of Object.entries(entries[kind])) put(join(compiled, entriesHome, entry + ".js"), `exports.${exported} = async () => { console.log('CALLED'); };\n`);
    put(join(compiled, entriesHome, "entity-smoke/diagnostics.js"), "exports.reportEntitySmokeFailure = (operation, reason) => console.error(JSON.stringify({operation, reason}));\n");
    const cli = join(repository, home, `build-${kind}-image/prepare-runtime.mjs`);
    body({ compiled, repository, cli, packages: orderedPackages, prepare: (args = []) => run(cli, ["--compiled-root", compiled, ...args]) });
  } finally { rmSync(temporary, { recursive: true, force: true }); }
}
function rejection(result, kind, phase, location = {}, writes = false) {
  assert.equal(result.status, 1, result.stderr);
  assert.equal(result.stdout, "");
  assert(!result.stderr.includes(canary));
  assert.deepEqual(JSON.parse(result.stderr), { scope: kind + "-runtime-preparation", verdict: "failed", code: "runtime-preparation-boundary-failed", phase, ...location, effect: writes ? "earlier-writes-possible" : "writes-not-started" });
}

for (const kind of Object.keys(entries)) {
  const feature = kind === "entity-smoke";
  test(`${kind}: actual Docker script closure, exports, manifest bytes and wrapper policies`, () => fixture(kind, ({ compiled, packages, prepare }) => {
    const prepared = prepare();
    assert.equal(prepared.status, 0, prepared.stderr);
    assert.equal(prepared.stderr, "");
    assert.equal(prepared.stdout, feature ? '{"scope":"entity-smoke-runtime-preparation","verdict":"prepared"}\n' : "");
    const imports = Object.entries(packages).flatMap(([name, exports]) => Object.keys(exports).map(key => name + (key === "." ? "" : key.slice(1))));
    assert.equal(readFileSync(join(compiled, feature ? "entity-smoke-payload.json" : "runtime-payload.json"), "utf8"), JSON.stringify({ required_imports: imports }) + (feature ? "\n" : ""));
    const probe = run("-e", ["console.log(JSON.stringify(" + JSON.stringify(imports) + ".map(name => require(name))))"], compiled);
    assert.equal(probe.status, 0, probe.stderr);
    const resolved = JSON.parse(probe.stdout);
    let resolvedIndex = 0;
    for (const [name, exports] of Object.entries(packages)) {
      const expectedExports = Object.fromEntries(Object.entries(exports).map(([key, target]) => [key, key === "." ? "./index.js" : key + (target.endsWith(".json") ? "" : "/index.js")]));
      assert.equal(readFileSync(join(compiled, "node_modules", name, "package.json"), "utf8"), JSON.stringify({ name, type: "commonjs", exports: expectedExports }, null, feature ? 0 : 2) + "\n");
      for (const [key, target] of Object.entries(exports)) {
        assert.deepEqual(resolved[resolvedIndex++], target.endsWith(".json") ? JSON.parse(readFileSync(join(root, target))) : { marker: target });
      }
    }
    for (const [entry, [exported, operation]] of Object.entries(entries[kind])) {
      const wrapper = join(compiled, entry + ".js");
      assert.equal(run(wrapper).stdout, "CALLED\n");
      const imported = run("-e", [`require(${JSON.stringify(wrapper)})`]);
      assert.equal(imported.status, 0, imported.stderr);
      assert.equal(imported.stdout, feature ? "" : "CALLED\n");
      put(join(compiled, entriesHome, entry + ".js"), `exports.${exported} = async () => { throw new Error('${canary}'); };\n`);
      const failed = run(wrapper);
      assert.equal(failed.status, 1);
      assert.equal(failed.stdout, "");
      assert.equal(failed.stderr, feature ? JSON.stringify({ operation, reason: "unknown" }) + "\n" : "");
    }
  }));
  test(`${kind}: argument, missing-entry and missing-export failures precede writes`, () => fixture(kind, ({ compiled, cli, prepare }) => {
    rejection(run(cli, ["--bad-" + canary, canary]), kind, "arguments");
    const entry = Object.keys(entries[kind])[0], target = join(compiled, entriesHome, entry + ".js"), bytes = readFileSync(target);
    rmSync(target); rejection(prepare(), kind, "compiled-entrypoint", { entrypoint: entry + (feature ? "" : ".js") }); put(target, bytes);
    rmSync(join(compiled, "packages/core/src/index.js"));
    rejection(prepare(), kind, "compiled-export", feature ? { package: "@kanbien/core", export: "." } : { compiledExport: "packages/core/src/index.js" });
    assert(!existsSync(join(compiled, "node_modules")));
  }));
  for (const [phase, blocked] of [["shim-directory", "node_modules"], ["shim-write", "node_modules/@kanbien/core/index.js"], ["manifest-write", "node_modules/@kanbien/core/package.json"], ["wrapper-write", Object.keys(entries[kind])[0] + ".js"], ["payload-manifest-write", feature ? "entity-smoke-payload.json" : "runtime-payload.json"]]) {
    test(`${kind}: ${phase} preserves safe location, write order and partial effect`, () => fixture(kind, ({ compiled, prepare }) => {
      if (phase === "shim-directory") put(join(compiled, blocked), canary); else mkdirSync(join(compiled, blocked), { recursive: true });
      const firstPackage = feature && phase === "shim-directory" ? "@kanbien/app-entity-smoke" : "@kanbien/core";
      const location = phase.startsWith("shim") ? { package: firstPackage, export: "." } : phase === "manifest-write" ? { package: "@kanbien/core" } : phase === "wrapper-write" ? { entrypoint: Object.keys(entries[kind])[0] + (feature ? "" : ".js") } : {};
      rejection(prepare(), kind, phase, location, true);
      if (phase === "wrapper-write") assert.equal(existsSync(join(compiled, feature ? "entity-smoke-payload.json" : "runtime-payload.json")), !feature);
      if (phase === "payload-manifest-write") assert.equal(existsSync(join(compiled, Object.keys(entries[kind])[0] + ".js")), feature);
    }));
  }
  test(`${kind}: Docker omission counterexample fails the real copied preparer`, () => fixture(kind, ({ repository, prepare }) => {
    rmSync(join(repository, home, "prepare-runtime-payload/assemble.mjs"));
    assert.notEqual(prepare().status, 0);
  }));
  for (const exception of contextExceptions) {
    test(`${kind}: excluded context exception ${exception} prevents preparation`, () => fixture(kind, ({ compiled, prepare }) => {
      assert.notEqual(prepare().status, 0);
      assert(!existsSync(join(compiled, "node_modules")));
    }, exception));
  }
}

test("feature: dry-run writes nothing; missing asset and asset-copy failure retain context", () => fixture("entity-smoke", ({ compiled, repository, prepare }) => {
  const before = snapshot(compiled);
  assert.equal(prepare(["--dry-run"]).stdout, '{"scope":"entity-smoke-runtime-preparation","verdict":"planned"}\n');
  assert.deepEqual(snapshot(compiled), before);
  assert(!existsSync(join(compiled, "node_modules")));
  const [key, target] = Object.entries(coreExports).find(([, target]) => target.endsWith(".json"));
  const asset = join(repository, "packages/core", target.slice(2)), bytes = readFileSync(asset);
  rmSync(asset); rejection(prepare(), "entity-smoke", "declarations", { reason: "workspace-export-source-missing", package: "@kanbien/core", export: key }); put(asset, bytes);
  mkdirSync(join(compiled, "node_modules/@kanbien/core", key.slice(2)), { recursive: true });
  rejection(prepare(), "entity-smoke", "asset-copy", { package: "@kanbien/core", export: key }, true);
}));

test("feature: malformed source manifest is rejected without exposing its contents", () => fixture("entity-smoke", ({ compiled, repository, prepare }) => {
  put(join(repository, "packages/core/package.json"), canary);
  rejection(prepare(), "entity-smoke", "declarations", { reason: "workspace-manifest-invalid-json" });
  assert(!existsSync(join(compiled, "node_modules")));
}));

test("renamed workload: same assembler resolves JS/JSON, validates mappings before writes and rejects symlinks", () => {
  const temporary = mkdtempSync(join(tmpdir(), "renamed-payload-"));
  try {
    put(join(temporary, "src/main.js"), "exports.marker = 17;\n"); put(join(temporary, "src/values.json"), '{"marker":23}');
    const mapping = { compiledRoot: temporary, packages: { "@example/renamed": { ".": "src/main.js", "./values.json": "src/values.json" } }, entrypoints: [{ target: "src/main.js", output: "renamed.js", source: "module.exports = require('./src/main.js');\n" }], manifest: { path: "renamed-payload.json", newline: true } };
    const initial = snapshot(temporary), state = {};
    assembleRuntimePayload({ ...mapping, dryRun: true }, state); assert.deepEqual(snapshot(temporary), initial);
    for (const invalid of [
      { compiledRoot: "" },
      { packages: { "../escape": { ".": "src/main.js" } } },
      { packages: { valid: { "./../escape": "src/main.js" } } },
      { packages: { valid: { ".": "../escape.js" } } },
      { packages: { valid: { ".": "/escape.js" } } },
      { packages: { valid: { ".": "src/values.json", "./index.json": "src/values.json" } } },
      { packages: { valid: {} } },
      { manifest: { path: "../escape.json", newline: true } },
      { entrypoints: [{ ...mapping.entrypoints[0], output: "../escape.js" }] },
      { entrypoints: [{ ...mapping.entrypoints[0], output: "renamed-payload.json" }] },
      { entrypoints: [{ ...mapping.entrypoints[0], output: "src/main.js" }] },
    ]) {
      assert.throws(() => assembleRuntimePayload({ ...mapping, ...invalid }, state));
      assert.deepEqual(state, { phase: "arguments", location: {}, writesStarted: false });
      assert.deepEqual(snapshot(temporary), initial);
    }
    symlinkSync(join(temporary, "src"), join(temporary, "node_modules"));
    assert.throws(() => assembleRuntimePayload(mapping, state)); assert.equal(state.writesStarted, false);
    rmSync(join(temporary, "node_modules"));
    symlinkSync(join(temporary, "src/main.js"), join(temporary, "linked.js"));
    assert.throws(() => assembleRuntimePayload({ ...mapping, packages: { valid: { ".": "linked.js" } } }, state));
    assert.equal(state.writesStarted, false);
    rmSync(join(temporary, "linked.js"));
    assembleRuntimePayload(mapping, state);
    const imported = run("-e", ["console.log(require('@example/renamed').marker, require('@example/renamed/values.json').marker)"], temporary);
    assert.equal(imported.status, 0, imported.stderr); assert.equal(imported.stdout, "17 23\n");
  } finally { rmSync(temporary, { recursive: true, force: true }); }
});
