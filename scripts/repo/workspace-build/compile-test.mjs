// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.compiler-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: testing
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove derived compiler inputs, original option behavior and finite failures with real disposable compilation.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.compiler
//     path: scripts/repo/workspace-build/compile.mjs

import { strict as assert } from "node:assert";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { compileProject, WorkspaceCompilationError } from "./compile.mjs";

const compilerHome = dirname(createRequire(import.meta.url).resolve("typescript/package.json"));
const repository = fileURLToPath(new URL("../../../", import.meta.url));
function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "workspace-compile-test-"));
  t.after(() => rmSync(root, { recursive: true }));
  function put(file, value) {
    mkdirSync(dirname(join(root, file)), { recursive: true });
    writeFileSync(join(root, file), typeof value === "string" ? value : JSON.stringify(value));
  }
  put("package.json", { name: "compiler-fixture", private: true, workspaces: ["packages/*"] });
  put("packages/leaf/package.json", { name: "@fixture/leaf", version: "0.0.0",
    exports: { ".": "./src/index.ts", "./public": "./src/public.ts" }, dependencies: { "@fixture/dep": "0.0.0" } });
  put("packages/dep/package.json", { name: "@fixture/dep", version: "0.0.0", exports: { ".": "./src/index.ts" } });
  put("packages/leaf/src/index.ts", 'export { value } from "@fixture/dep";\n');
  put("packages/leaf/src/public.ts", 'export const another = 17;\n');
  put("packages/dep/src/index.ts", 'export const value: number = 42;\n');
  put("src/main.ts", 'import { value } from "@fixture/leaf"; export const result = value;\n');
  put("base.json", { compilerOptions: { target: "ES2022", module: "CommonJS", moduleResolution: "Node10",
    strict: true, noEmitOnError: true, types: [], rootDir: ".", outDir: "build" }, include: ["src/**/*.ts"] });
  put("project.json", { extends: "./base.json" });
  mkdirSync(join(root, "node_modules"));
  symlinkSync(compilerHome, join(root, "node_modules/typescript"), "dir");
  return { root, put, options: { root, project: "project.json", selection: { roots: ["@fixture/leaf"] } } };
}

test("real compilation preserves inherited options and includes all payload exports only when requested", t => {
  const { root, options } = fixture(t);
  const first = compileProject(options);
  assert.equal(first.status, 0);
  assert.match(readFileSync(join(root, "build/src/main.js"), "utf8"), /require\("@fixture\/leaf"\)/);
  assert.equal(existsSync(join(root, "build/packages/leaf/src/public.js")), false);
  assert.equal(compileProject({ ...options, payload: true,
    compilerArguments: ["--outDir", "payload", "--incremental", "false"] }).status, 0);
  assert.match(readFileSync(join(root, "payload/packages/leaf/src/public.js"), "utf8"), /another = 17/);
  assert.equal(existsSync(join(root, "payload/src/main.js")), true);
  assert.equal(existsSync(join(root, "payload/packages/dep/src/index.js")), true);
});

test("declaration and ES module options remain compiler-owned rather than forced to CommonJS", t => {
  const { root, put, options } = fixture(t);
  put("project.json", { extends: "./base.json", compilerOptions: {
    module: "ESNext", moduleResolution: "Bundler", declaration: true, emitDeclarationOnly: true,
  } });
  assert.equal(compileProject({ ...options, payload: true }).status, 0);
  assert.equal(existsSync(join(root, "build/src/main.js")), false);
  assert.match(readFileSync(join(root, "build/src/main.d.ts"), "utf8"), /export declare const result: number/);
});

test("neutral compiler rejects inherited handwritten aliases before invoking TypeScript", t => {
  const { root, put, options } = fixture(t);
  const inherited = JSON.parse(readFileSync(join(root, "base.json"), "utf8"));
  inherited.compilerOptions.paths = { "PRIVATE_CANARY": ["src/main.ts"] };
  put("base.json", inherited);
  let calls = 0;
  assert.throws(() => compileProject(options, { runCompiler() { calls++; } }), error =>
    error instanceof WorkspaceCompilationError && error.code === "compiler-aliases-must-be-derived"
      && error.effect === "not-started" && !String(error).includes("PRIVATE_CANARY"));
  assert.equal(calls, 0);
  assert.equal(existsSync(join(root, "build")), false);
});

test("real Node type resolution survives temporary config relocation", t => {
  const { root, put, options } = fixture(t);
  mkdirSync(join(root, "node_modules/@types"));
  symlinkSync(join(repository, "node_modules/@types/node"), join(root, "node_modules/@types/node"), "dir");
  symlinkSync(join(repository, "node_modules/undici-types"), join(root, "node_modules/undici-types"), "dir");
  put("project.json", { extends: "./base.json", compilerOptions: { types: ["node"] } });
  put("src/main.ts", 'import { readFileSync } from "node:fs"; export const count = Buffer.from("ok").length; export { readFileSync };\n');
  assert.equal(compileProject(options).status, 0);
  assert.equal(existsSync(join(root, "build/src/main.js")), true);
});

test("actual entity workspace runtime project compiles with derived aliases and original Node types", t => {
  const output = mkdtempSync(join(tmpdir(), "actual-workspace-compiler-"));
  t.after(() => rmSync(output, { recursive: true }));
  assert.equal(compileProject({ root: repository, project: "apps/entity-smoke/tsconfig.runtime-test.json",
    selection: { roots: ["@kanbien/app-entity-smoke"], includeRootDevDependencies: true },
    compilerArguments: ["--outDir", output, "--incremental", "false"], payload: true }).status, 0);
  assert.equal(existsSync(join(output, "apps/entity-smoke/src/index.js")), true);
  assert.equal(existsSync(join(output, "packages/core/src/config/index.js")), true);
});

test("temporary config derives exact selected aliases and is private and removed after one invocation", t => {
  const { root, options } = fixture(t);
  let calls = 0, temporary;
  const result = compileProject({ ...options, payload: true }, { runCompiler(executable, argv, spawnOptions) {
    calls++;
    assert.equal(executable, process.execPath);
    assert.equal(argv[0], join(compilerHome, "bin/tsc"));
    assert.equal(argv[1], "--project");
    temporary = argv[2];
    assert.equal(statSync(temporary).mode & 0o777, 0o600);
    const generated = JSON.parse(readFileSync(temporary, "utf8"));
    assert.equal(generated.extends, join(root, "project.json"));
    assert.equal(generated.compilerOptions.baseUrl, root);
    assert(generated.compilerOptions.typeRoots.includes(join(root, "node_modules/@types")));
    assert.deepEqual(generated.compilerOptions.paths, {
      "@fixture/dep": ["packages/dep/src/index.ts"], "@fixture/leaf": ["packages/leaf/src/index.ts"],
      "@fixture/leaf/public": ["packages/leaf/src/public.ts"],
    });
    assert.deepEqual(generated.files, ["packages/dep/src/index.ts", "packages/leaf/src/index.ts",
      "packages/leaf/src/public.ts", "src/main.ts"].map(file => join(root, file)));
    assert.deepEqual(generated.include, []);
    assert.deepEqual(spawnOptions, { cwd: root, encoding: "utf8", stdio: "pipe" });
    return { status: 0, stdout: "SECRET_OUTPUT", stderr: "SECRET_ERROR" };
  } });
  assert.equal(calls, 1);
  assert.equal(existsSync(dirname(temporary)), false);
  assert.equal(JSON.stringify(result).includes("SECRET_"), false);
});

test("preparation rejects unsupported overrides, symlink roots and references before a compiler process", t => {
  const { root, put, options } = fixture(t);
  let calls = 0;
  const dependencies = { runCompiler() { calls++; return { status: 0 }; } };
  for (const compilerArguments of [["--project", "SECRET_PATH"], ["--outDir"], ["--incremental", "yes"],
    ["--outDir", "one", "--outDir", "two"], ["--watch", "true"]]) {
    assert.throws(() => compileProject({ ...options, compilerArguments }, dependencies), error =>
      error instanceof WorkspaceCompilationError && error.code === "compiler-arguments-invalid" && error.effect === "not-started");
  }
  const aliases = mkdtempSync(join(tmpdir(), "workspace-compiler-alias-"));
  t.after(() => rmSync(aliases, { recursive: true }));
  symlinkSync(root, join(aliases, "root"), "dir");
  assert.throws(() => compileProject({ ...options, root: join(aliases, "root") }, dependencies), error =>
    error.code === "compiler-project-invalid" && error.effect === "not-started");
  put("project.json", { extends: "./base.json", references: [{ path: "./packages/leaf" }] });
  assert.throws(() => compileProject(options, dependencies), error => error.code === "compiler-project-references-unsupported");
  assert.equal(calls, 0);
});

test("real compiler failures retain exit status without removing existing output or disclosing source", t => {
  const { root, put, options } = fixture(t);
  put("src/main.ts", 'export const SECRET_SOURCE: number = "wrong";\n');
  put("build/keep.txt", "caller-owned");
  assert.throws(() => compileProject(options), error => {
    assert.equal(error.code, "compiler-failed");
    assert.equal(error.exitCode, 1);
    assert.equal(error.effect, "outputs-possible");
    assert.equal(String(error).includes("SECRET_SOURCE"), false);
    assert.deepEqual(error.diagnosticCodes, [2322]);
    assert.equal(error.diagnosticsTruncated, false);
    assert.equal(JSON.stringify(error).includes(root), false);
    return true;
  });
  assert.equal(readFileSync(join(root, "build/keep.txt"), "utf8"), "caller-owned");
});

test("process errors and interruption remain finite uncertain effects with temporary cleanup", t => {
  const { options } = fixture(t);
  for (const [child, code] of [[{ status: null, signal: "SIGTERM" }, "compiler-interrupted"],
    [{ error: new Error("SECRET_NATIVE") }, "compiler-process-unavailable"],
    [{ status: 7, stderr: "SECRET_NATIVE" }, "compiler-failed"]]) {
    let temporary, calls = 0;
    assert.throws(() => compileProject(options, { runCompiler(_command, argv) {
      calls++; temporary = dirname(argv[2]); return child;
    } }), error => {
      assert.equal(error.code, code);
      assert.equal(error.effect, "outputs-possible");
      assert.equal(String(error).includes("SECRET_"), false);
      if (child.status === 7) assert.equal(error.exitCode, 7);
      return true;
    });
    assert.equal(calls, 1);
    assert.equal(existsSync(temporary), false);
  }
});
