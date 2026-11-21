// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.command-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: testing
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove discovered workspace command bindings, finite rejection and actual CLI failure projection.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.command
//     path: scripts/repo/workspace-build/script.mjs

import { strict as assert } from "node:assert";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { WorkspaceCompilationError } from "./compile.mjs";
import { runWorkspaceCompiler, workspaceCompilerOptions } from "./script.mjs";
import { loadWorkspaceGraph } from "./declarations.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "workspace-command-"));
  t.after(() => rmSync(root, { recursive: true }));
  writeFileSync(join(root, "package.json"), JSON.stringify({ workspaces: ["packages/*", "packages/outer/nested/*"] }));
  for (const [directory, name] of [["outer", "@renamed/outer"], ["outer/nested/leaf", "@renamed/leaf"]]) {
    mkdirSync(join(root, "packages", directory), { recursive: true });
    writeFileSync(join(root, "packages", directory, "package.json"), JSON.stringify({ name }));
  }
  return root;
}

test("project owner derives from discovered manifests, including nearest nested workspace", t => {
  const root = fixture(t);
  assert.deepEqual(workspaceCompilerOptions(["--project", "packages/outer/nested/leaf/tsconfig.json", "--development", "--payload",
    "--outDir", "output", "--incremental", "false"], root), {
    root, project: "packages/outer/nested/leaf/tsconfig.json", payload: true,
    compilerArguments: ["--outDir", "output", "--incremental", "false"],
    selection: { roots: ["@renamed/leaf"], includeRootDevDependencies: true },
  });
  assert.deepEqual(workspaceCompilerOptions(["--project", "packages/outer/tsconfig.json"], root).selection,
    { roots: ["@renamed/outer"], includeRootDevDependencies: false });
});

test("bad arguments and unowned projects reject before compilation without supplied values", t => {
  const root = fixture(t);
  let calls = 0;
  for (const args of [[], ["--project"], ["--project", "SECRET"], ["--unknown", "SECRET"],
    ["--project", "packages/outer/x.json", "--development", "--development"], ["--project", "../SECRET/x.json"]]) {
    const outcome = runWorkspaceCompiler(args, { root, compile() { calls++; } });
    assert.equal(outcome.exitCode, 1);
    assert.equal(outcome.diagnostic.effect, "not-started");
    assert.equal(JSON.stringify(outcome).includes("SECRET"), false);
  }
  assert.equal(calls, 0);
});

test("command preserves compiler exit and numeric meaning without native exceptions", t => {
  const root = fixture(t), args = ["--project", "packages/outer/project.json"];
  assert.deepEqual(runWorkspaceCompiler(args, { root, compile() {} }), { exitCode: 0 });
  assert.deepEqual(runWorkspaceCompiler(args, { root, compile() {
    throw new WorkspaceCompilationError("compiler-failed", "outputs-possible", 2, [2322]);
  } }), { exitCode: 2, diagnostic: { code: "compiler-failed", effect: "outputs-possible", diagnosticCodes: [2322], diagnosticsTruncated: false } });
  const unknown = runWorkspaceCompiler(args, { root, compile() { throw new Error("SECRET_NATIVE"); } });
  assert.equal(unknown.diagnostic.effect, "unknown");
  assert.equal(JSON.stringify(unknown).includes("SECRET"), false);
});

test("actual CLI invalid input exits unsuccessfully with only finite report", () => {
  const result = spawnSync(process.execPath, [fileURLToPath(new URL("./script.mjs", import.meta.url)), "--SECRET"], { encoding: "utf8" });
  assert.equal(result.status, 1);
  assert.equal(result.stdout, "");
  assert.deepEqual(JSON.parse(result.stderr), { code: "compiler-arguments-invalid", effect: "not-started", diagnosticCodes: [], diagnosticsTruncated: false });
});

test("actual migrated workspace commands derive their owner and leave no handwritten test aliases", () => {
  const root = fileURLToPath(new URL("../../../", import.meta.url));
  const graph = loadWorkspaceGraph(root), scripts = JSON.parse(readFileSync(join(root, "package.json"), "utf8")).scripts;
  const commands = Object.values(scripts).filter(value => value.startsWith("node scripts/repo/workspace-build/script.mjs --project "));
  assert(commands.length > 0);
  for (const command of commands) {
    const argv = command.split(" && ")[0].split(" ").slice(2);
    const options = workspaceCompilerOptions(argv, root);
    const owner = graph.packages.get(options.selection.roots[0]);
    assert(options.project.startsWith(owner.directory + "/"));
    assert.equal(options.selection.includeRootDevDependencies, true);
    const config = JSON.parse(readFileSync(join(root, options.project), "utf8"));
    assert.equal(config.compilerOptions?.paths, undefined);
    if (!options.project.endsWith("check.json")) assert.equal(options.payload, true);
  }
  for (const record of graph.packages.values()) {
    for (const name of readdirSync(join(root, record.directory))) {
      if (!/^tsconfig\.(?:runtime-test|integration-test|check)\.json$/.test(name)) continue;
      const config = JSON.parse(readFileSync(join(root, record.directory, name), "utf8"));
      assert.equal(config.compilerOptions?.paths, undefined, "Workspace test aliases must derive from manifests.");
    }
  }
});
