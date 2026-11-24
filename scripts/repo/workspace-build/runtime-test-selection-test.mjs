// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.runtime-test-selection-test
//   version: 1
//   status: active
//   created_on: "2026-11-22"
//   updated_on: "2026-11-22"
//   layer: 06.shared
//   domain: testing
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Prove source-aware runtime-test selection includes static import dependants and falls closed when ownership is unsafe.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.runtime-test-selection
//     path: scripts/repo/workspace-build/runtime-test-selection.mjs

import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { RuntimeTestSelectionError, selectAffectedRuntimeTests } from "./runtime-test-selection.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "runtime-test-selection-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const write = (path, body) => {
    const file = join(root, path);
    mkdirSync(dirname(file), { recursive: true });
    writeFileSync(file, body);
  };
  write("packages/example/src/shared.ts", "export const shared = 1;\n");
  write("packages/example/src/leaf.ts", 'import { shared } from "./shared.js"; export const leaf = shared;\n');
  write("packages/example/tests/helpers/leaf-fixture.ts", 'import { leaf } from "../../src/leaf.js"; export { leaf };\n');
  write("packages/example/tests/leaf-runtime.test.ts", 'import { leaf } from "./helpers/leaf-fixture.js"; void leaf;\n');
  write("packages/example/tests/other-runtime.test.ts", "export {};\n");
  return { root, write };
}

function select(root, changedPaths) {
  return selectAffectedRuntimeTests({ root, sourceDirectory: "packages/example/src", testDirectory: "packages/example/tests", changedPaths });
}

test("selects direct and transitive static import dependants through test helpers", t => {
  const { root } = fixture(t);
  assert.deepEqual(select(root, ["packages/example/src/leaf.ts"]), {
    mode: "affected", reasons: ["static-relative-imports"], testFiles: ["packages/example/tests/leaf-runtime.test.ts"],
  });
  assert.deepEqual(select(root, ["packages/example/src/shared.ts"]).testFiles, ["packages/example/tests/leaf-runtime.test.ts"]);
});

test("keeps a changed runtime test itself and falls closed for unowned changes", t => {
  const { root } = fixture(t);
  assert.deepEqual(select(root, ["packages/example/tests/other-runtime.test.ts"]).testFiles, ["packages/example/tests/other-runtime.test.ts"]);
  const full = select(root, ["packages/example/src/newly-added.ts"]);
  assert.equal(full.mode, "full");
  assert.deepEqual(full.testFiles, ["packages/example/tests/leaf-runtime.test.ts", "packages/example/tests/other-runtime.test.ts"]);
});

test("does not narrow an unresolved or dynamic dependency graph", t => {
  const { root, write } = fixture(t);
  write("packages/example/src/dynamic.ts", "export const load = () => import('./shared.js');\n");
  const full = select(root, ["packages/example/src/shared.ts"]);
  assert.equal(full.mode, "full");
  assert.deepEqual(full.reasons, ["dependency-analysis-unsafe"]);
});

test("rejects unsafe changed paths and source symlinks without treating them as accepted input", t => {
  const { root } = fixture(t);
  assert.throws(() => select(root, ["../synthetic-canary.ts"]), error => error instanceof RuntimeTestSelectionError
    && error.code === "runtime-test-selection-changed-path-invalid");
  symlinkSync(join(root, "packages/example/src/shared.ts"), join(root, "packages/example/src/shared-link.ts"));
  assert.throws(() => select(root, ["packages/example/src/shared.ts"]), error => error instanceof RuntimeTestSelectionError
    && error.code === "runtime-test-selection-symlink");
});
