// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.runnable-program.build-inputs-test
//   version: 3
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove existing dependency approval bindings and rejection before compilation or packaging.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.runnable-program.build-inputs
//     path: scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { stringify } from "yaml";
import { readProgramBuildInputs, ProgramBuildInputError } from "./build-inputs.mjs";
import { compileProgram } from "./compile.mjs";
import { WorkspaceCompilationError } from "../../../../repo/workspace-build/compile.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "program-build-inputs-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  function put(path, value) {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), typeof value === "string" ? value : JSON.stringify(value));
  }
  put("package.json", { workspaces: ["packages/*"] });
  for (const [directory, name, dependencies] of [
    ["leaf", "@example/leaf", { "@example/value": "0.0.0", "driver": "^1.0.0" }],
    ["value", "@example/value", {}], ["unapproved", "@example/unapproved", {}],
  ]) {
    put(`packages/${directory}/package.json`, { name, exports: { ".": "./src/index.ts" }, dependencies });
    put(`packages/${directory}/src/index.ts`, "export const value = 17;\n");
  }
  put("program.tsconfig.json", { compilerOptions: { module: "CommonJS" } });
  put("program.ts", "export const handler = async () => true;\n");
  const declaration = { schema: "deploy/runnable-program-contract/v1", id: "renamed-candidate", version: 1,
    dependency_bindings: { application: { workspace_package: "@example/leaf" },
      values: { workspace_package: "@example/value" }, database: { external_packages: ["driver"] } },
    runnable_programs: [{ id: "renamed-ledger", source_entrypoint: "program.ts", entrypoint: "handler.js", runtime_executable: "node", build: { kind: "workspace-typescript", typescript_project: "program.tsconfig.json" },
      approved_dependencies: ["application", "values", "database"], observed_dependencies: ["application", "values", "database"], forbidden_dependencies: ["other"] }] };
  const save = () => put("program.yml", stringify(declaration)); save();
  const run = (options = {}) => readProgramBuildInputs(root, { programId: "renamed-ledger", contractPath: "program.yml", ...options });
  return { root, put, declaration, save, run };
}

test("actual read-only program CLI emits the shared projection and finite errors", t => {
  const { root, run } = fixture(t), script = fileURLToPath(new URL("./build-inputs.mjs", import.meta.url));
  const result = spawnSync(process.execPath, [script, "--program", "renamed-ledger", "--contract", "program.yml"], { cwd: root, encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  assert.deepEqual(JSON.parse(result.stdout), run());
  for (const args of [["--PRIVATE_CANARY"], ["--program", "absent", "--contract", "program.yml"],
    ["--program", "renamed-ledger", "--contract", "../PRIVATE_CANARY"]]) {
    const failed = spawnSync(process.execPath, [script, ...args], { cwd: root, encoding: "utf8" });
    assert.equal(failed.status, 1); assert.equal(failed.stderr, "");
    assert.deepEqual(Object.keys(JSON.parse(failed.stdout)), ["error"]);
    assert(!failed.stdout.includes("PRIVATE_CANARY"));
  }
});
function rejects(run, code) {
  assert.throws(run, error => error.code === code && error.message === code && !String(error).includes("PRIVATE_CANARY"));
}

test("renamed program derives only existing approved package bindings and declared external roots", t => {
  const { run } = fixture(t), result = run();
  assert.equal(result.project, "program.tsconfig.json");
  assert.deepEqual(result.runtimeEntry, { executionKind: "process", source: "program.ts", compiled: "program.js", output: "handler.js" });
  assert.deepEqual(result.selection, { roots: ["@example/leaf", "@example/value"], allowedPackages: ["@example/leaf", "@example/value"] });
  assert.deepEqual(result.inputs.externalDependencies, ["driver"]);
  assert.deepEqual(result.inputs.compilerPaths, { "@example/leaf": ["packages/leaf/src/index.ts"], "@example/value": ["packages/value/src/index.ts"] });
  assert(result.manifestPaths.includes("program.yml"));
  assert(result.manifestPaths.includes("program.tsconfig.json"));
});

test("managed handler projection rejects unsafe selections before payload preparation", t => {
  const { declaration, save, run } = fixture(t), program = declaration.runnable_programs[0];
  program.execution_kind = "managed-handler"; program.handler_export = "handler"; save();
  assert.deepEqual(run().runtimeEntry, { executionKind: "managed-handler", source: "program.ts", compiled: "program.js", output: "handler.js", handlerExport: "handler" });
  for (const [field, value, code] of [["handler_export", "a.b", "program-build-handler-invalid"],
    ["source_entrypoint", "../PRIVATE_CANARY.ts", "program-build-entrypoint-invalid"],
    ["entrypoint", "../PRIVATE_CANARY.js", "program-build-entrypoint-invalid"],
    ["execution_kind", "PRIVATE_CANARY", "program-build-execution-invalid"],
    ["runtime_executable", "python", "program-build-handler-invalid"]]) {
    const original = program[field]; program[field] = value; save(); rejects(run, code); program[field] = original;
  }
  program.execution_kind = "process"; save(); rejects(run, "program-build-handler-invalid");
});

test("missing bindings and transitive dependencies outside approval reject", t => {
  const { declaration, save, run } = fixture(t);
  delete declaration.dependency_bindings.application; save();
  rejects(run, "program-build-binding-invalid");
  declaration.dependency_bindings.application = { workspace_package: "@example/leaf" };
  declaration.runnable_programs[0].approved_dependencies = ["application", "database"];
  declaration.runnable_programs[0].observed_dependencies = ["application", "database"]; save();
  rejects(run, "workspace-dependency-not-approved");
});

test("unapproved external dependency and known observed/forbidden conflicts reject", t => {
  const { declaration, save, run } = fixture(t);
  declaration.dependency_bindings.database.external_packages = ["other-driver"]; save();
  rejects(run, "program-build-external-dependency-not-approved");
  declaration.runnable_programs[0].forbidden_dependencies.push("database"); save();
  rejects(run, "program-build-dependency-not-approved");
  declaration.runnable_programs[0].forbidden_dependencies = [];
  declaration.runnable_programs[0].observed_dependencies.push("other"); save();
  rejects(run, "program-build-dependency-not-approved");
});

test("ambiguous or misclassified bindings and missing workspace packages reject", t => {
  const { declaration, save, run } = fixture(t);
  for (const binding of [{ workspace_package: "@example/missing" },
    { workspace_package: "@example/leaf", external_packages: ["driver"] },
    { external_packages: ["@example/leaf"] }, { external_packages: ["driver", "driver"] }]) {
    declaration.dependency_bindings.application = binding; save();
    rejects(run, binding.workspace_package === "@example/missing" ? "workspace-dependency-unresolved" : "program-build-binding-invalid");
  }
});

test("strict YAML rejects duplicate keys, multiple documents, unknown tags and aliases without native details", t => {
  const { root, put, run } = fixture(t), original = readFileSync(join(root, "program.yml"), "utf8");
  for (const text of [original + "schema: PRIVATE_CANARY\n", original + "---\nPRIVATE_CANARY\n",
    "schema: !PRIVATE_CANARY value\n", "schema: &PRIVATE_CANARY [value]\nid: *PRIVATE_CANARY\n", "schema: [PRIVATE_CANARY\n"]) {
    put("program.yml", text);
    assert.throws(run, error => error instanceof ProgramBuildInputError && error.code === "program-build-declaration-invalid"
      && !String(error).includes("PRIVATE_CANARY"));
  }
});

test("invalid selection, duplicate program IDs and invalid project paths fail before compilation", t => {
  const { root, put, declaration, save, run } = fixture(t);
  rejects(() => readProgramBuildInputs(root, null), "program-build-selection-invalid");
  rejects(() => run({ programId: "missing" }), "program-build-record-missing");
  rejects(() => run({ contractPath: "../PRIVATE_CANARY" }), "program-build-path-invalid");
  declaration.runnable_programs.push(structuredClone(declaration.runnable_programs[0])); save();
  rejects(run, "program-build-records-invalid");
  declaration.runnable_programs.pop();
  declaration.runnable_programs[0].build.typescript_project = "../PRIVATE_CANARY.json"; save();
  rejects(run, "program-build-project-invalid");
  declaration.runnable_programs[0].build.typescript_project = "missing.json"; save();
  rejects(run, "program-build-source-unreadable");
  declaration.runnable_programs[0].build.typescript_project = "linked.json"; save();
  symlinkSync(join(root, "program.tsconfig.json"), join(root, "linked.json"));
  rejects(run, "program-build-source-symlink");
  put("program.yml", "[]\n");
  rejects(run, "program-build-declaration-invalid");
});

test("all three actual programs derive their current distinct package and external boundaries", () => {
  const root = fileURLToPath(new URL("../../../../../", import.meta.url));
  const bootstrap = readProgramBuildInputs(root, { programId: "kanbien-core-server" });
  const baseline = readProgramBuildInputs(root, { programId: "kanbien-core-server-persistence" });
  const feature = readProgramBuildInputs(root, { programId: "kanbien-entity-smoke" });
  assert.equal(bootstrap.inputs.packageNames.length, 8);
  assert.deepEqual(bootstrap.inputs.externalDependencies, []);
  assert.equal(baseline.inputs.packageNames.length, 11);
  assert.equal(feature.inputs.packageNames.length, 11);
  assert(baseline.inputs.packageNames.includes("@kanbien/platform-adapter-aws-observability-cloudwatch"));
  assert(!feature.inputs.packageNames.includes("@kanbien/platform-adapter-aws-observability-cloudwatch"));
  assert(feature.inputs.packageNames.includes("@kanbien/app-entity-smoke"));
  assert(!baseline.inputs.packageNames.includes("@kanbien/app-entity-smoke"));
  assert.deepEqual(feature.inputs.externalDependencies, ["@aws-sdk/rds-signer", "pg"]);
  assert.deepEqual(feature.inputs.compilerPaths["@kanbien/platform-server/main"], ["platform/server/src/main.ts"]);
});

test("managed handler projects isolate each declared scheduling program", () => {
  const root = fileURLToPath(new URL("../../../../../", import.meta.url));
  for (const scope of ["kanbien-core-server-persistence", "kanbien-entity-smoke"]) {
    for (const purpose of ["dispatch", "worker"]) {
      const id = `${scope}-scheduling-${purpose}`;
      const selected = readProgramBuildInputs(root, { programId: id });
      const project = JSON.parse(readFileSync(join(root, selected.project), "utf8"));
      const isolated = candidate => {
        assert.deepEqual(candidate.include, [`./${id}.handler.ts`]);
        assert.equal(candidate.compilerOptions.strict, true);
        assert.equal(candidate.compilerOptions.noEmitOnError, true);
        assert.equal(candidate.compilerOptions.paths, undefined);
      };
      isolated(project);
      assert.throws(() => isolated({ ...project, include: ["./*.ts"] }));
      assert.equal(selected.runtimeEntry.executionKind, "managed-handler");
      assert.equal(selected.runtimeEntry.handlerExport, "handler");
      assert.equal(selected.runtimeEntry.source, `infra/04.deploy/03.product/entrypoints/${id}.handler.ts`);
      assert(selected.inputs.packageNames.includes("@kanbien/platform-adapter-aws-runtime-lambda"));
      assert.equal(selected.inputs.packageNames.includes("@kanbien/app-entity-smoke"), scope === "kanbien-entity-smoke");
      assert(!selected.inputs.packageNames.includes("@kanbien/platform-adapter-aws-runtime-ecs-fargate"));
    }
  }
});

test("renamed program command invokes the shared compiler with declared selection", t => {
  const { root, put, declaration } = fixture(t);
  put("infra/04.deploy/03.product/entrypoints/runnable-program-index.yml", stringify(declaration));
  const calls = [];
  assert.deepEqual(compileProgram(["--program", "renamed-ledger", "--outDir", "output", "--incremental", "false"], {
    root, compile(options) { calls.push(options); },
  }), { exitCode: 0 });
  assert.deepEqual(calls, [{ root, project: "program.tsconfig.json", payload: true,
    selection: { roots: ["@example/leaf", "@example/value"], allowedPackages: ["@example/leaf", "@example/value"] },
    compilerArguments: ["--outDir", "output", "--incremental", "false"] }]);
});

test("program command rejects before invocation and preserves compiler failure", t => {
  const { root, put, declaration } = fixture(t);
  put("infra/04.deploy/03.product/entrypoints/runnable-program-index.yml", stringify(declaration));
  let calls = 0;
  for (const args of [[], ["--program"], ["--unknown", "PRIVATE_CANARY"], ["--program", "missing"],
    ["--program", "renamed-ledger", "--program", "renamed-ledger"]]) {
    const result = compileProgram(args, { root, compile() { calls++; } });
    assert.equal(result.exitCode, 1); assert.equal(result.diagnostic.effect, "not-started");
    assert(!JSON.stringify(result).includes("PRIVATE_CANARY"));
  }
  assert.equal(calls, 0);
  const failed = compileProgram(["--program", "renamed-ledger"], { root,
    compile() { throw new WorkspaceCompilationError("compiler-failed", "outputs-possible", 2, [2322]); },
  });
  assert.deepEqual(failed, { exitCode: 2, diagnostic: { code: "compiler-failed", effect: "outputs-possible", diagnosticCodes: [2322], diagnosticsTruncated: false } });
  const unknown = compileProgram(["--program", "renamed-ledger"], { root, compile() { throw new Error("PRIVATE_CANARY"); } });
  assert.deepEqual(unknown, { exitCode: 1, diagnostic: { code: "program-build-boundary-failed", effect: "unknown", diagnosticCodes: [], diagnosticsTruncated: false } });
});
