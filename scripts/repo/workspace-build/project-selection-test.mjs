// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.project-selection-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: testing
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Prove explicit project roots select declared workspace closures without approving discovered imports.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.project-selection
//     path: scripts/repo/workspace-build/project-selection.mjs

import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readdirSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { projectWorkspaceInputs } from "./project-selection.mjs";
import { runWorkspaceCompiler, workspaceCompilerOptions } from "./script.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "project-workspaces-"));
  t.after(() => rmSync(root, { recursive: true }));
  const put = (path, value) => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), typeof value === "string" ? value : JSON.stringify(value));
  };
  put("package.json", { private: true, workspaces: ["packages/*"] });
  for (const name of ["picked", "dependency", "unapproved"]) {
    put(`packages/${name}/package.json`, { name: `@different/${name}`, exports: { ".": "./src/index.ts" },
      ...(name === "picked" ? { dependencies: { "@different/dependency": "0.0.0" } } : {}) });
    put(`packages/${name}/src/index.ts`, "export const value = 1;\n");
  }
  put("base.json", { compilerOptions: { types: [], strict: true }, include: ["packages/picked/src/**/*.ts"] });
  put("project.json", { extends: "./base.json" });
  return { root, put };
}

test("explicit inherited roots select renamed owners and normal runtime dependencies, not imports", t => {
  const { root, put } = fixture(t);
  put("packages/picked/src/index.ts", 'import "@different/unapproved";\n');
  const result = projectWorkspaceInputs(root, "project.json");
  assert.deepEqual(result.selection, { roots: ["@different/picked"] });
  assert.deepEqual(result.inputs.packageNames, ["@different/dependency", "@different/picked"]);
  assert.deepEqual(result.rootFiles, ["packages/picked/src/index.ts"]);
  assert.deepEqual(result.unownedRootFiles, []);
});

test("adding, changing and removing explicit roots changes selection without another mapping", t => {
  const { root, put } = fixture(t);
  put("project.json", { include: ["packages/picked/src/**/*.ts", "packages/unapproved/src/**/*.ts"] });
  assert.deepEqual(projectWorkspaceInputs(root, "project.json").selection.roots, ["@different/picked", "@different/unapproved"]);
  put("project.json", { files: ["packages/unapproved/src/index.ts"] });
  assert.deepEqual(projectWorkspaceInputs(root, "project.json").inputs.packageNames, ["@different/unapproved"]);
  rmSync(join(root, "packages/unapproved/src/index.ts"));
  assert.throws(() => projectWorkspaceInputs(root, "project.json"), error => error.code === "workspace-project-source-unavailable");
});

test("unowned roots require the caller's explicit bounded prefix", t => {
  const { root, put } = fixture(t);
  put("infra/entrypoints/probe.ts", "export {};\n");
  put("project.json", { files: ["packages/picked/src/index.ts", "infra/entrypoints/probe.ts"] });
  assert.throws(() => projectWorkspaceInputs(root, "project.json"), error => error.code === "workspace-project-root-unowned");
  assert.deepEqual(projectWorkspaceInputs(root, "project.json", { unownedRootPrefixes: ["infra/entrypoints/"] }).unownedRootFiles,
    ["infra/entrypoints/probe.ts"]);
  for (const prefix of ["/", "../", "infra/../", "infra/entrypoints", "infra//"]) {
    assert.throws(() => projectWorkspaceInputs(root, "project.json", { unownedRootPrefixes: [prefix] }), error => error.code === "workspace-project-invalid");
  }
});

test("malformed options, projects, root escapes and symlinks reject without writes or native content", t => {
  const { root, put } = fixture(t);
  const before = readdirSync(root).sort();
  for (const options of [null, [], { unexpected: "PRIVATE_CANARY" }, { unownedRootPrefixes: null }]) {
    assert.throws(() => projectWorkspaceInputs(root, "project.json", options), error => error.code === "workspace-project-invalid");
  }
  assert.throws(() => projectWorkspaceInputs(root, "../PRIVATE_CANARY.json"), error => error.code === "workspace-project-root-escaped");
  assert.deepEqual(readdirSync(root).sort(), before);
  put("project.json", "{PRIVATE_CANARY");
  assert.throws(() => projectWorkspaceInputs(root, "project.json"), error => error.code === "workspace-project-invalid" && !String(error).includes("PRIVATE_CANARY"));
  put("project.json", { files: ["packages/picked/src/link.ts"] });
  symlinkSync(join(root, "packages/picked/src/index.ts"), join(root, "packages/picked/src/link.ts"));
  assert.throws(() => projectWorkspaceInputs(root, "project.json"), error => error.code === "workspace-source-symlink");
  put("project.json", { files: [], include: [], references: [{ path: "./base.json" }] });
  assert.throws(() => projectWorkspaceInputs(root, "project.json"), error => error.code === "workspace-project-invalid");
  put("infra/probe.ts", "export {};\n");
  put("project.json", { files: ["infra/probe.ts"] });
  assert.throws(() => projectWorkspaceInputs(root, "project.json", { unownedRootPrefixes: ["infra/"] }), error => error.code === "workspace-project-workspaces-empty");
});

test("CLI project-roots selection is explicit, retains overrides and cannot combine test approval", t => {
  const { root } = fixture(t);
  const argv = ["--project-roots", "--project", "project.json", "--payload", "--outDir", "output", "--incremental", "false"];
  const options = workspaceCompilerOptions(argv, root);
  assert.deepEqual(options.selection, { roots: ["@different/picked"] });
  assert.deepEqual(options.compilerArguments, ["--outDir", "output", "--incremental", "false"]);
  assert.equal(options.payload, true);
  let calls = 0;
  for (const args of [[...argv, "--development"], ["--project", "project.json", "--unowned-root-prefix", "infra/"]]) {
    const result = runWorkspaceCompiler(args, { root, compile() { calls++; } });
    assert.equal(result.diagnostic.code, "compiler-arguments-invalid");
    assert.equal(result.diagnostic.effect, "not-started");
  }
  assert.equal(calls, 0);
});

test("actual legacy and diagnostic projects derive nonempty declared closures", () => {
  const root = fileURLToPath(new URL("../../../", import.meta.url));
  for (const project of ["platform/server/tsconfig.image.json", "scripts/repo/diagnostic-coverage/tsconfig.json"]) {
    const result = projectWorkspaceInputs(root, project, { unownedRootPrefixes: ["infra/04.deploy/03.product/entrypoints/"] });
    assert(result.selection.roots.length > 1);
    assert(result.inputs.packageNames.includes("@kanbien/core"));
    assert(result.unownedRootFiles.length > 0);
  }
});

test("only explicit generation may defer missing JSON, never TS, directories or symlinks", t => {
  const { root, put } = fixture(t);
  put("packages/picked/package.json", { name: "@different/picked", exports: { ".": "./src/index.ts", "./catalog.json": "./generated/catalog.json" } });
  assert.throws(() => projectWorkspaceInputs(root, "project.json"), error => error.code === "workspace-export-source-missing");
  const options = { allowMissingJsonAssets: true };
  assert.equal(projectWorkspaceInputs(root, "project.json", options).inputs.packages["@different/picked"]["./catalog.json"], "packages/picked/generated/catalog.json");
  assert.equal(workspaceCompilerOptions(["--project-roots", "--project", "project.json", "--generated-json-assets"], root).selection.allowMissingJsonAssets, true);
  mkdirSync(join(root, "packages/picked/generated/catalog.json"), { recursive: true });
  assert.throws(() => projectWorkspaceInputs(root, "project.json", options), error => error.code === "workspace-export-source-missing");
  rmSync(join(root, "packages/picked/generated/catalog.json"), { recursive: true });
  symlinkSync(join(root, "packages/picked/src/index.ts"), join(root, "packages/picked/generated/catalog.json"));
  assert.throws(() => projectWorkspaceInputs(root, "project.json", options), error => error.code === "workspace-source-symlink");
  rmSync(join(root, "packages/picked/generated/catalog.json"));
  rmSync(join(root, "packages/picked/src/index.ts"));
  put("project.json", { files: ["packages/dependency/src/index.ts"] });
  put("packages/dependency/package.json", { name: "@different/dependency", exports: { ".": "./src/index.ts" }, dependencies: { "@different/picked": "0.0.0" } });
  assert.throws(() => projectWorkspaceInputs(root, "project.json", options), error => error.code === "workspace-export-source-missing");
});
