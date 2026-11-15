// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.declarations-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.declarations
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Prove declaration-derived build inputs, boundary rejection and finite read failures with isolated workspaces.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.declarations
//     path: scripts/repo/workspace-build/declarations.mjs

import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, test } from "node:test";
import { deriveWorkspaceInputs, loadWorkspaceGraph, selectWorkspaceProject, WorkspaceDeclarationError } from "./declarations.mjs";

const temporary = [];
afterEach(() => { for (const path of temporary.splice(0)) rmSync(path, { recursive: true, force: true }); });
function file(root, path, value) {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), typeof value === "string" ? value : JSON.stringify(value));
}
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "workspace-declarations-")); temporary.push(root);
  file(root, "package.json", { workspaces: ["packages/*", "apps/*", "adapters/*/*"] });
  pkg(root, "packages/values", "@sample/values");
  pkg(root, "packages/test-kit", "@sample/test-kit");
  pkg(root, "packages/transitive-test", "@sample/transitive-test");
  pkg(root, "apps/ledger", "@sample/ledger", {
    dependencies: { "@sample/values": "0.0.0", "external-driver": "^1.0.0" },
    devDependencies: { "@sample/test-kit": "0.0.0" },
  });
  change(root, "packages/values", { devDependencies: { "@sample/transitive-test": "0.0.0" } });
  return root;
}
function pkg(root, directory, name, extra = {}) {
  file(root, `${directory}/package.json`, { name, version: "0.0.0", exports: { ".": "./src/index.ts" }, ...extra });
  file(root, `${directory}/src/index.ts`, "export const value = 17;\n");
}
function change(root, directory, fields) {
  const path = `${directory}/package.json`;
  file(root, path, { ...JSON.parse(readFileSync(join(root, path))), ...fields });
}
const derive = (root, options = {}) => deriveWorkspaceInputs(loadWorkspaceGraph(root), { roots: ["@sample/ledger"], ...options });
function rejects(operation, code) {
  assert.throws(operation, error => error instanceof WorkspaceDeclarationError && error.code === code
    && error.message === code && !String(error).includes("PRIVATE_CANARY"));
}
function tree(root, directory = "") {
  return readdirSync(join(root, directory), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name)).flatMap(entry => {
    const path = directory ? `${directory}/${entry.name}` : entry.name;
    return entry.isDirectory() ? tree(root, path) : [[path, readFileSync(join(root, path), "utf8")]];
  });
}

test("runtime closure derives exact aliases, exports and external roots without writing", () => {
  const root = fixture(), before = tree(root), inputs = derive(root);
  assert.deepEqual(inputs.packageNames, ["@sample/ledger", "@sample/values"]);
  assert.deepEqual(inputs.compilerPaths, {
    "@sample/ledger": ["apps/ledger/src/index.ts"], "@sample/values": ["packages/values/src/index.ts"],
  });
  assert.deepEqual(inputs.packages, {
    "@sample/ledger": { ".": "apps/ledger/src/index.js" }, "@sample/values": { ".": "packages/values/src/index.js" },
  });
  assert.deepEqual(inputs.externalDependencies, ["external-driver"]);
  assert.deepEqual(inputs.manifestPaths, ["apps/ledger/package.json", "package.json", "packages/values/package.json"]);
  assert.deepEqual(tree(root), before);
});

test("workspace project selection rejects invalid or unowned paths without exposing values", () => {
  const graph = loadWorkspaceGraph(fixture());
  assert.equal(selectWorkspaceProject(graph, "apps/ledger/tests/new-case.ts"), "@sample/ledger");
  rejects(() => selectWorkspaceProject(null, "PRIVATE_CANARY"), "workspace-graph-invalid");
  for (const value of [null, "", "PRIVATE_CANARY\0"]) rejects(() => selectWorkspaceProject(graph, value), "workspace-project-invalid");
  for (const value of ["../PRIVATE_CANARY", "apps/ledger-other/PRIVATE_CANARY"]) rejects(() => selectWorkspaceProject(graph, value), "workspace-project-owner-missing");
});

test("tests add only selected roots' dev dependencies, not every transitive test package", () => {
  const inputs = derive(fixture(), { includeRootDevDependencies: true });
  assert.deepEqual(inputs.packageNames, ["@sample/ledger", "@sample/test-kit", "@sample/values"]);
  assert(!inputs.packageNames.includes("@sample/transitive-test"));
});

test("added, changed and removed exports follow declarations, including public JSON assets", () => {
  const root = fixture();
  file(root, "packages/values/src/count.ts", "export const count = 3;\n");
  file(root, "packages/values/assets/catalog.json", { schema: "test/v1" });
  change(root, "packages/values", { exports: { ".": "./src/index.ts", "./count": "./src/count.ts", "./catalog.json": "./assets/catalog.json" } });
  let inputs = derive(root);
  assert.deepEqual(inputs.compilerPaths["@sample/values/count"], ["packages/values/src/count.ts"]);
  assert.equal(inputs.packages["@sample/values"]["./catalog.json"], "packages/values/assets/catalog.json");
  assert(!inputs.sourceFiles.some(path => path.endsWith(".json")));
  change(root, "packages/values", { exports: { ".": "./src/count.ts" } });
  inputs = derive(root);
  assert.deepEqual(inputs.compilerPaths["@sample/values"], ["packages/values/src/count.ts"]);
  assert.equal(inputs.compilerPaths["@sample/values/count"], undefined);
  assert.equal(inputs.packages["@sample/values"]["./catalog.json"], undefined);
});

test("new differently named nested workspace is discovered without a mapping patch", () => {
  const root = fixture();
  pkg(root, "adapters/local/archive", "archive-store", { dependencies: { "@sample/values": "0.0.0" } });
  const inputs = derive(root, { roots: ["archive-store"] });
  assert.deepEqual(inputs.compilerPaths["archive-store"], ["adapters/local/archive/src/index.ts"]);
  assert.deepEqual(inputs.packageNames, ["@sample/values", "archive-store"]);
});

test("discovery is not approval and unknown roots are not external dependencies", () => {
  const root = fixture();
  rejects(() => deriveWorkspaceInputs(loadWorkspaceGraph(root), null), "workspace-selection-invalid");
  rejects(() => deriveWorkspaceInputs(null, { roots: ["@sample/ledger"] }), "workspace-graph-invalid");
  rejects(() => derive(root, { allowedPackages: ["@sample/ledger"] }), "workspace-dependency-not-approved");
  rejects(() => derive(root, { roots: ["PRIVATE_CANARY"] }), "workspace-selection-invalid");
  rejects(() => derive(root, { roots: ["@sample/missing"] }), "workspace-dependency-unresolved");
  assert.deepEqual(derive(root, { allowedPackages: ["@sample/ledger", "@sample/values"] }).packageNames, ["@sample/ledger", "@sample/values"]);
});

test("missing locked workspace cannot silently become an external package", () => {
  const root = fixture();
  change(root, "apps/ledger", { dependencies: { "@sample/removed": "0.0.0" } });
  file(root, "package-lock.json", { packages: { "node_modules/@sample/removed": { link: true, resolved: "packages/removed" } } });
  rejects(() => derive(root), "workspace-dependency-unresolved");
  rmSync(join(root, "package-lock.json"));
  change(root, "apps/ledger", { dependencies: { "@sample/removed": "workspace:*" } });
  rejects(() => derive(root), "workspace-dependency-unresolved");
});

test("cycles terminate without dropping selected manifests", () => {
  const root = fixture();
  change(root, "packages/values", { dependencies: { "@sample/ledger": "0.0.0" } });
  assert.deepEqual(derive(root).packageNames, ["@sample/ledger", "@sample/values"]);
});

test("unsupported and malformed exports reject instead of guessing an alias", () => {
  const root = fixture();
  for (const [exports, code] of [
    [undefined, "workspace-exports-missing"], [{}, "workspace-exports-missing"],
    [{ "./*": "./src/index.ts" }, "workspace-export-key-unsupported"],
    [{ ".": { import: "./src/index.ts" } }, "workspace-export-target-unsupported"],
    [{ ".": "./src/PRIVATE_CANARY.d.ts" }, "workspace-export-target-unsupported"],
    [{ ".": "./../PRIVATE_CANARY.ts" }, "workspace-export-target-unsupported"],
    [{ ".": "/PRIVATE_CANARY.ts" }, "workspace-export-target-unsupported"],
    [{ ".": "./src/PRIVATE_CANARY.ts" }, "workspace-export-source-missing"],
  ]) {
    change(root, "packages/values", { exports });
    rejects(() => derive(root), code);
  }
});

test("missing declared source retains only checked package and export identity", () => {
  const root = fixture();
  change(root, "packages/values", { exports: { "./count": "./src/PRIVATE_CANARY.ts" } });
  assert.throws(() => derive(root), error => {
    assert.equal(error.code, "workspace-export-source-missing");
    assert.deepEqual(error.location, { package: "@sample/values", export: "./count" });
    assert(!JSON.stringify(error).includes("PRIVATE_CANARY"));
    assert(Object.isFrozen(error.location));
    return true;
  });
});

test("unsupported dependency kinds and malformed dependency contents fail closed", () => {
  const root = fixture();
  for (const dependencies of [null, [], "PRIVATE_CANARY", { x: 1 }]) {
    change(root, "apps/ledger", { dependencies });
    rejects(() => derive(root), "workspace-dependencies-invalid");
  }
  change(root, "apps/ledger", { dependencies: {}, optionalDependencies: { x: "1" } });
  rejects(() => derive(root), "workspace-dependency-kind-unsupported");
  change(root, "apps/ledger", { optionalDependencies: {}, peerDependencies: { x: "1" } });
  rejects(() => derive(root), "workspace-dependency-kind-unsupported");
});

test("duplicate names, malformed JSON and unsupported root globs retain finite diagnostics", () => {
  const root = fixture();
  pkg(root, "apps/duplicate", "@sample/ledger");
  rejects(() => loadWorkspaceGraph(root), "workspace-package-name-duplicate");
  file(root, "apps/duplicate/package.json", "PRIVATE_CANARY:not-json");
  rejects(() => loadWorkspaceGraph(root), "workspace-manifest-invalid-json");
  file(root, "package.json", { workspaces: ["packages/**"] });
  rejects(() => loadWorkspaceGraph(root), "workspace-pattern-unsupported");
});

test("symlinked workspace, manifest and export targets are rejected without traversal", () => {
  for (const kind of ["workspace", "manifest", "export"]) {
    const root = fixture();
    if (kind === "workspace") symlinkSync(join(root, "packages/values"), join(root, "apps/PRIVATE_CANARY"));
    if (kind === "manifest") {
      rmSync(join(root, "apps/ledger/package.json"));
      symlinkSync(join(root, "packages/values/package.json"), join(root, "apps/ledger/package.json"));
    }
    if (kind === "export") {
      rmSync(join(root, "packages/values/src/index.ts"));
      symlinkSync(join(root, "apps/ledger/src/index.ts"), join(root, "packages/values/src/index.ts"));
    }
    rejects(() => derive(root), "workspace-source-symlink");
  }
});

test("symlinked repository root is rejected before its manifests are read", () => {
  const root = fixture();
  const parent = mkdtempSync(join(tmpdir(), "workspace-root-link-")); temporary.push(parent);
  symlinkSync(root, join(parent, "PRIVATE_CANARY"));
  rejects(() => loadWorkspaceGraph(join(parent, "PRIVATE_CANARY")), "workspace-source-symlink");
});

test("actual repository declarations resolve feature and PostgreSQL roots without runtime test dependencies", () => {
  const root = fileURLToPath(new URL("../../../", import.meta.url));
  const graph = loadWorkspaceGraph(root);
  const inputs = deriveWorkspaceInputs(graph, { roots: ["@kanbien/app-entity-smoke", "@kanbien/platform-adapter-aws-persistence-postgresql"] });
  assert(inputs.packageNames.includes("@kanbien/core"));
  assert(!inputs.packageNames.includes("@kanbien/platform-testing"));
  assert.deepEqual(inputs.externalDependencies, ["@aws-sdk/rds-signer", "pg"]);
  assert.equal(inputs.packages["@kanbien/core"]["./config/diagnostics.v1.json"], "packages/core/src/config/contract/reporting/diagnostics.v1.json");
  assert(!Object.keys(inputs.compilerPaths).some(key => key.includes("*")));
});
