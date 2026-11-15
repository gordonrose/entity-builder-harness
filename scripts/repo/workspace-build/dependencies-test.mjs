// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.dependencies-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.declarations
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Prove manifest ownership against literal direct and relative import bypasses using differently named workspaces.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.dependencies
//     path: scripts/repo/workspace-build/dependencies.mjs

import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, test } from "node:test";
import { inspectWorkspaceDependencies } from "./dependencies.mjs";
import { WorkspaceDeclarationError } from "./declarations.mjs";

const temporary = [];
afterEach(() => { for (const root of temporary.splice(0)) rmSync(root, { recursive: true, force: true }); });
function file(root, path, value) {
  mkdirSync(dirname(join(root, path)), { recursive: true });
  writeFileSync(join(root, path), typeof value === "string" ? value : JSON.stringify(value));
}
function pkg(root, directory, name, fields = {}) {
  file(root, `${directory}/package.json`, { name, exports: { ".": "./src/index.ts" }, ...fields });
  file(root, `${directory}/src/index.ts`, "export const value = 1;\n");
}
function change(root, directory, fields) {
  const path = `${directory}/package.json`;
  file(root, path, { ...JSON.parse(readFileSync(join(root, path), "utf8")), ...fields });
}
function fixture() {
  const root = mkdtempSync(join(tmpdir(), "workspace-dependencies-")); temporary.push(root);
  file(root, "package.json", { workspaces: ["apps/*", "packages/*"], devDependencies: { typescript: "5.9.3", yaml: "2.9.1" } });
  pkg(root, "apps/receipt", "@renamed/receipt");
  pkg(root, "packages/amount", "@renamed/amount");
  pkg(root, "packages/assertions", "@renamed/assertions");
  return root;
}
const inspect = root => inspectWorkspaceDependencies(root);
const codes = root => inspect(root).findings.map(row => row.code);
const undeclared = "WORKSPACE_DEPENDENCY_UNDECLARED";

test("direct and relative runtime edges both require the importing package's declaration", () => {
  const root = fixture();
  file(root, "apps/receipt/src/index.ts", 'import "@renamed/amount";\nexport * from "../../../packages/amount/src/index";\n');
  assert.deepEqual(inspect(root).findings, [
    { code: undeclared, path: "apps/receipt/src/index.ts", line: 1 },
    { code: undeclared, path: "apps/receipt/src/index.ts", line: 2 },
  ]);
  change(root, "apps/receipt", { dependencies: { "@renamed/amount": "0.0.0" } });
  assert.deepEqual(codes(root), []);
});

test("root test development dependencies do not authorise runtime or transitive workspace source", () => {
  const root = fixture();
  change(root, "apps/receipt", { devDependencies: { "@renamed/assertions": "0.0.0" } });
  file(root, "apps/receipt/tests/check.test.ts", 'import "@renamed/assertions";\n');
  assert.deepEqual(codes(root), []);
  file(root, "apps/receipt/src/index.ts", 'import "@renamed/assertions";\n');
  assert.deepEqual(codes(root), [undeclared]);
  file(root, "apps/receipt/src/index.ts", 'export const value = 1;\n');
  file(root, "packages/assertions/src/index.ts", 'import "@renamed/receipt";\n');
  assert.deepEqual(inspect(root).findings, [{ code: undeclared, path: "packages/assertions/src/index.ts", line: 1 }]);
});

test("runtime cannot launder development dependencies through its own or another package's test helpers", () => {
  const root = fixture();
  change(root, "apps/receipt", { dependencies: { "@renamed/amount": "0.0.0" }, devDependencies: { "@renamed/assertions": "0.0.0" } });
  file(root, "apps/receipt/tests/helper.ts", 'import "@renamed/assertions";\n');
  file(root, "packages/amount/tests/helper.ts", 'export const testValue = 1;\n');
  file(root, "apps/receipt/src/index.ts", 'import "../tests/helper";\nimport "../../../packages/amount/tests/helper";\n');
  assert.deepEqual(inspect(root).findings, [1, 2].map(line => ({ code: "WORKSPACE_RUNTIME_TEST_DEPENDENCY", path: "apps/receipt/src/index.ts", line })));
});

test("a runtime source folder called fixtures or tests does not authorise development dependencies", () => {
  const root = fixture();
  change(root, "apps/receipt", { devDependencies: { "@renamed/assertions": "0.0.0" } });
  file(root, "apps/receipt/src/fixtures/sample.ts", 'import "@renamed/assertions";\n');
  file(root, "apps/receipt/src/tests/sample.ts", 'import "@renamed/assertions";\n');
  assert.deepEqual(inspect(root).findings.map(row => row.path), ["apps/receipt/src/fixtures/sample.ts", "apps/receipt/src/tests/sample.ts"]);
  assert(codes(root).every(code => code === undeclared));
});

test("imported test entrypoints use selected test closure but cannot borrow root tooling dependencies", () => {
  const root = fixture();
  change(root, "apps/receipt", { devDependencies: { "@renamed/assertions": "0.0.0" } });
  change(root, "packages/assertions", { dependencies: { "@renamed/amount": "0.0.0" } });
  file(root, "apps/receipt/tests/check.test.ts", 'import "../../../infra/probe";\n');
  file(root, "infra/probe.ts", 'import "@renamed/amount";\n');
  assert.deepEqual(codes(root), []);
  file(root, "infra/probe.ts", 'import "yaml";\n');
  assert.deepEqual(inspect(root).findings, [{ code: undeclared, path: "infra/probe.ts", line: 1 }]);
  change(root, "apps/receipt", { devDependencies: { yaml: "2.9.1" } });
  assert.deepEqual(codes(root), []);
});

test("root-owned tooling retains its own declarations without widening workspace dependencies", () => {
  const root = fixture();
  file(root, "apps/receipt/tests/check.test.ts", 'import "../../../scripts/repo/helper.mjs";\n');
  file(root, "scripts/repo/helper.mjs", 'import ts from "typescript";\nimport "yaml";\n');
  assert.deepEqual(codes(root), []);
  file(root, "scripts/repo/helper.mjs", 'import "PRIVATE_UNDECLARED_CANARY";\n');
  const report = inspect(root);
  assert.deepEqual(report.findings, [{ code: undeclared, path: "scripts/repo/helper.mjs", line: 1 }]);
  assert(!JSON.stringify(report).includes("PRIVATE_UNDECLARED_CANARY"));
  file(root, "apps/receipt/src/index.ts", 'import "../../../scripts/repo/helper.mjs";\n');
  assert(codes(root).includes("WORKSPACE_SOURCE_OWNER_MISSING"));
});

test("renamed package additions, export changes and removals are observed, never auto-approved", () => {
  const root = fixture();
  pkg(root, "packages/new-name", "@another/fresh");
  file(root, "apps/receipt/src/index.ts", 'import "@another/fresh";\n');
  assert.deepEqual(codes(root), [undeclared]);
  change(root, "apps/receipt", { dependencies: { "@another/fresh": "0.0.0" } });
  assert.deepEqual(codes(root), []);
  file(root, "apps/receipt/src/index.ts", 'import "@another/fresh/private";\n');
  assert.deepEqual(codes(root), ["WORKSPACE_EXPORT_UNDECLARED", "WORKSPACE_IMPORT_UNRESOLVED"]);
  file(root, "packages/new-name/src/private.ts", "export const secret = 1;\n");
  change(root, "packages/new-name", { exports: { ".": "./src/index.ts", "./private": "./src/private.ts" } });
  assert.deepEqual(codes(root), []);
  rmSync(join(root, "packages/new-name/package.json"));
  file(root, "package-lock.json", { packages: { "node_modules/@another/fresh": { link: true, resolved: "packages/new-name" } } });
  assert.throws(() => inspect(root), error => error instanceof WorkspaceDeclarationError && error.code === "workspace-dependency-unresolved");
});

test("literal import types, import-equals, dynamic imports and createRequire aliases are checked", () => {
  const root = fixture();
  file(root, "apps/receipt/src/index.ts", [
    'import {createRequire} from "node:module";',
    'const load = createRequire(import.meta.url);',
    'type Value = import("@renamed/amount");',
    'import other = require("@renamed/amount");',
    'void import("@renamed/amount");',
    'load("@renamed/amount");',
    'const selected = "@renamed/amount"; void import(selected);',
  ].join("\n"));
  const report = inspect(root);
  assert.deepEqual(report.findings.map(row => row.line), [3, 4, 5, 6]);
  assert(report.findings.every(row => row.code === undeclared));
  assert.equal(report.computedImports, 1);
});

test("broken relative imports, runtime unowned entrypoints and malformed source fail closed", () => {
  const root = fixture();
  file(root, "apps/receipt/src/index.ts", 'import "./missing";\nimport "../../../infra/probe";\n');
  file(root, "infra/probe.ts", 'export const value = 1;\n');
  assert.deepEqual(codes(root), ["WORKSPACE_IMPORT_UNRESOLVED", "WORKSPACE_SOURCE_OWNER_MISSING"]);
  file(root, "apps/receipt/src/index.ts", "export const = ;\n");
  assert.deepEqual(codes(root), ["WORKSPACE_SOURCE_SYNTAX_INVALID"]);
});

test("symlinked workspace source and unsupported declarations cannot disappear from the inventory", () => {
  const root = fixture();
  symlinkSync(join(root, "packages/amount/src/index.ts"), join(root, "apps/receipt/src/linked.ts"));
  assert.deepEqual(codes(root), ["WORKSPACE_SOURCE_SYMLINK"]);
  change(root, "packages/amount", { exports: { ".": { default: "./src/index.ts" } } });
  assert.throws(() => inspect(root), error => error instanceof WorkspaceDeclarationError && error.code === "workspace-export-target-unsupported");
});

test("imported unowned entrypoint and tooling symlinks are rejected before reading their bodies", () => {
  const root = fixture();
  file(root, "apps/receipt/tests/check.test.ts", 'import "../../../infra/probe";\nimport "../../../scripts/repo/tool.mjs";\n');
  file(root, "private.ts", 'import "PRIVATE_LINK_TARGET_CANARY";\n');
  mkdirSync(join(root, "infra")); mkdirSync(join(root, "scripts/repo"), { recursive: true });
  symlinkSync(join(root, "private.ts"), join(root, "infra/probe.ts"));
  symlinkSync(join(root, "private.ts"), join(root, "scripts/repo/tool.mjs"));
  const report = inspect(root);
  assert.deepEqual(report.findings, ["infra/probe.ts", "scripts/repo/tool.mjs"].map(path => ({ code: "WORKSPACE_SOURCE_SYMLINK", path, line: 1 })));
  assert(!JSON.stringify(report).includes("PRIVATE_LINK_TARGET_CANARY"));
});
