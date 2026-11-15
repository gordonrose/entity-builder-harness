// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.runtime-packages-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.runtime-packages
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Prove isolated runtime imports, JSON assets, fresh-output changes and bounded failures.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.runtime-packages
//     path: scripts/repo/workspace-build/runtime-packages.mjs

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, test } from "node:test";
import { planRuntimePackages, prepareWorkspaceRuntime, RuntimePackageError, writeRuntimePackages, copyRuntimePackageAssets } from "./runtime-packages.mjs";

const temporary = [];
afterEach(() => { for (const root of temporary.splice(0)) rmSync(root, { recursive: true, force: true }); });
function put(root, path, value) {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), typeof value === "string" ? value : JSON.stringify(value));
}
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "runtime-workspaces-")); temporary.push(root);
  const repository = join(root, "repository"), compiledRoot = join(root, "compiled");
  mkdirSync(compiledRoot);
  put(repository, "package.json", { workspaces: ["packages/*"] });
  put(repository, "packages/count/package.json", { name: "@fixture/count", exports: { ".": "./src/index.ts", "./label": "./src/label.ts" } });
  put(repository, "packages/count/src/index.ts", "export const count = 37;");
  put(repository, "packages/count/src/label.ts", "export const label = 'unchanged';");
  put(repository, "packages/catalog/package.json", { name: "catalog", exports: { ".": "./values.json", "./named": "./values.json", "./literal.json": "./values.json" }, dependencies: { "@fixture/count": "1" } });
  put(repository, "packages/catalog/values.json", { category: "first" });
  put(compiledRoot, "packages/count/src/index.js", "exports.count = 37;\n");
  put(compiledRoot, "packages/count/src/label.js", "exports.label = 'unchanged';\n");
  return { root, repository, compiledRoot, selection: { roots: ["catalog"] } };
}
function run(compiledRoot, expression) {
  return spawnSync(process.execPath, ["-e", expression], { cwd: compiledRoot, encoding: "utf8", env: { ...process.env, NODE_PATH: "" }, timeout: 10000 });
}
function rejects(operation, code) {
  assert.throws(operation, error => error instanceof RuntimePackageError && error.code === code && error.message === code
    && !String(error).includes("PRIVATE_CANARY"));
}

test("real CommonJS and JSON default/subpath imports work without checkout dependencies", () => {
  const options = fixture(), state = {};
  assert.deepEqual(prepareWorkspaceRuntime(options, state).packageNames, ["@fixture/count", "catalog"]);
  assert(!existsSync(join(options.repository, "node_modules")));
  const child = run(options.compiledRoot, "console.log(JSON.stringify([require('@fixture/count').count, require('@fixture/count/label').label, require('catalog'), require('catalog/named'), require('catalog/literal.json')]))");
  assert.equal(child.status, 0, child.stderr);
  assert.deepEqual(JSON.parse(child.stdout), [37, "unchanged", { category: "first" }, { category: "first" }, { category: "first" }]);
  assert.equal(state.writesStarted, true);
});

test("changed and removed exports leave no stale export in a fresh output", () => {
  const options = fixture(); prepareWorkspaceRuntime(options);
  put(options.repository, "packages/count/package.json", { name: "@fixture/count", exports: { ".": "./src/label.ts" } });
  put(options.repository, "packages/catalog/values.json", { category: "changed" });
  const fresh = join(options.root, "fresh");
  put(fresh, "packages/count/src/label.js", "exports.label = 'changed';\n");
  prepareWorkspaceRuntime({ ...options, compiledRoot: fresh });
  assert(!existsSync(join(fresh, "node_modules/@fixture/count/label")));
  const child = run(fresh, "console.log(JSON.stringify([require('@fixture/count').label,require('catalog').category])); try { require('@fixture/count/label'); process.exit(2); } catch (e) { if(e.code !== 'ERR_PACKAGE_PATH_NOT_EXPORTED') throw e; }");
  assert.equal(child.status, 0, child.stderr);
  assert.deepEqual(JSON.parse(child.stdout), ["changed", "changed"]);
});

test("missing compiled input rejects before writes with exact phase and location", () => {
  const options = fixture(), state = {};
  rmSync(join(options.compiledRoot, "packages/count/src/label.js"));
  rejects(() => prepareWorkspaceRuntime(options, state), "runtime-package-source-missing");
  assert.equal(state.phase, "compiled-export");
  assert.deepEqual(state.location, { package: "@fixture/count", export: "./label", compiledExport: "packages/count/src/label.js" });
  assert.equal(state.writesStarted, false);
  assert(!existsSync(join(options.compiledRoot, "node_modules")));
});

test("symlinked compiled roots, ancestors and asset roots reject before writes", () => {
  const options = fixture();
  symlinkSync(options.compiledRoot, join(options.root, "compiled-link"), "dir");
  symlinkSync(options.repository, join(options.root, "repository-link"), "dir");
  const packages = { count: { ".": "packages/count/src/index.js" } };
  for (const path of ["compiled-link", "compiled-link/nested"]) rejects(() => planRuntimePackages({ compiledRoot: join(options.root, path), packages }), "runtime-package-source-symlink");
  rejects(() => planRuntimePackages({ compiledRoot: options.compiledRoot, assetRoot: join(options.root, "repository-link"), packages: { catalog: { ".": "packages/catalog/values.json" } } }), "runtime-package-source-symlink");
  assert(!existsSync(join(options.compiledRoot, "node_modules")));
});

test("native write failure retains finite failure and attempted-write state", () => {
  const options = fixture(), state = {};
  put(options.compiledRoot, "node_modules", "PRIVATE_CANARY");
  rejects(() => prepareWorkspaceRuntime(options, state), "runtime-package-write-failed");
  assert.equal(state.phase, "shim-directory");
  assert.equal(state.writesStarted, true);
  assert.deepEqual(state.location, { package: "@fixture/count", export: "." });
  assert.equal(readFileSync(join(options.compiledRoot, "node_modules"), "utf8"), "PRIVATE_CANARY");
});

test("deferred catalogue assets are not copied until explicitly released after generation", () => {
  const options = fixture();
  const plan = planRuntimePackages({ compiledRoot: options.compiledRoot, assetRoot: options.repository,
    packages: { catalog: { ".": "packages/catalog/values.json" }, count: { ".": "packages/count/src/index.js" } } });
  rmSync(join(options.repository, "packages/catalog/values.json"));
  writeRuntimePackages(plan, {}, { deferJsonAssets: true });
  assert(!existsSync(join(options.compiledRoot, "node_modules/catalog/index.json")));
  assert.equal(run(options.compiledRoot, "require('count')").status, 0);
  rejects(() => copyRuntimePackageAssets(plan), "runtime-package-source-missing");
  put(options.repository, "packages/catalog/values.json", { category: "regenerated" });
  copyRuntimePackageAssets(plan);
  const before = readFileSync(join(options.compiledRoot, "node_modules/catalog/index.json"), "utf8");
  put(options.repository, "packages/catalog/values.json", { category: "unaccepted" });
  writeRuntimePackages(plan, {}, { deferJsonAssets: true });
  assert.equal(readFileSync(join(options.compiledRoot, "node_modules/catalog/index.json"), "utf8"), before);
  assert.deepEqual(JSON.parse(before), { category: "regenerated" });
});
