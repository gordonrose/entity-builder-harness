// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.prepare-runtime-payload.managed-handler
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove managed payload selection and rejection through the actual declaration reader and assembler.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: github.workflow.publish-kanbien-core-platform-scheduling
//     path: .github/workflows/publish-kanbien-core-platform-scheduling.yml
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { createRequire } from "node:module";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { parse, stringify } from "yaml";
import { prepareManagedHandler, runManagedHandler } from "./managed-handler.mjs";
import { copyProgramFixture } from "../prepare-runtime-dependencies/program-fixture.mjs";
import { readProgramBuildInputs } from "../../20-build/runnable-program-contract/build-inputs.mjs";
const source = fileURLToPath(new URL("../../../../../", import.meta.url));
const program = "kanbien-core-server-persistence-scheduling-worker";
const index = "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml";
function put(path, body) { mkdirSync(dirname(path), { recursive: true }); writeFileSync(path, body); }
async function fixture(body, selectedProgram = program) {
  const temporary = mkdtempSync(join(tmpdir(), "managed-payload-"));
  const root = join(temporary, "source"), compiledRoot = join(temporary, "compiled");
  try {
    copyProgramFixture(root, selectedProgram);
    const selected = readProgramBuildInputs(source, { programId: selectedProgram });
    for (const exports of Object.values(selected.inputs.packages)) for (const target of Object.values(exports)) {
      if (target.endsWith(".js")) put(join(compiledRoot, target), "exports.fixture = true;\n");
    }
    put(join(compiledRoot, selected.runtimeEntry.compiled), "exports.handler = async event => ({ preserved: event });\n");
    return await body({ root, compiledRoot, selected, temporary });
  } finally { rmSync(temporary, { recursive: true, force: true }); }
}
for (const selected of ["kanbien-core-server-persistence-scheduling-dispatch", program,
  "kanbien-entity-smoke-scheduling-dispatch", "kanbien-entity-smoke-scheduling-worker"]) {
  test(selected + ": exact declared export and public package closure", async () => {
    await fixture(async ({ root, compiledRoot, selected: build }) => {
      const result = prepareManagedHandler({ root, compiledRoot, programId: selected });
      assert.deepEqual(result, { schema: "deploy/managed-handler-payload/v1", verdict: "prepared", program_id: selected, handler: "handler.handler" });
      const require = createRequire(join(compiledRoot, "probe.js"));
      const loaded = require("./handler.js");
      assert.deepEqual(await loaded.handler({ marker: "preserved" }), { preserved: { marker: "preserved" } });
      const payload = JSON.parse(readFileSync(join(compiledRoot, "runtime-payload.json")));
      assert.deepEqual(payload.required_imports, Object.entries(build.inputs.packages).flatMap(([name, exports]) => Object.keys(exports).map(key => name + (key === "." ? "" : key.slice(1)))));
    }, selected);
  });
}
test("dry run validates without adding wrappers", () => fixture(({ root, compiledRoot }) => {
  assert.equal(prepareManagedHandler({ root, compiledRoot, programId: program, dryRun: true }).verdict, "planned");
  assert.throws(() => readFileSync(join(compiledRoot, "handler.js")), { code: "ENOENT" });
}));
test("missing compiled target rejects before writes", () => fixture(({ root, compiledRoot, selected }) => {
  rmSync(join(compiledRoot, selected.runtimeEntry.compiled));
  const result = runManagedHandler(["--program", program, "--compiled-root", compiledRoot], root);
  assert.equal(result.exitCode, 1); assert.equal(result.report.phase, "compiled-entrypoint");
  assert.equal(result.report.effect, "writes-not-started");
  assert.throws(() => readFileSync(join(compiledRoot, "handler.js")), { code: "ENOENT" });
}));
test("missing export cannot silently become a callable handler", () => fixture(({ root, compiledRoot, selected }) => {
  put(join(compiledRoot, selected.runtimeEntry.compiled), "exports.other = () => {};\n");
  prepareManagedHandler({ root, compiledRoot, programId: program });
  assert.throws(() => createRequire(join(compiledRoot, "probe.js"))("./handler.js"), /MANAGED_HANDLER_EXPORT_INVALID/);
}));
test("process substitution and malformed handler metadata reject", () => fixture(({ root, compiledRoot }) => {
  const path = join(root, index), original = readFileSync(path, "utf8");
  for (const change of [value => value.execution_kind = "process", value => value.handler_export = "handler;private-canary", value => value.entrypoint = "../escape.js"]) {
    const document = parse(original), selected = document.runnable_programs.find(item => item.id === program);
    change(selected); put(path, stringify(document));
    const outcome = runManagedHandler(["--program", program, "--compiled-root", compiledRoot], root);
    assert.equal(outcome.exitCode, 1); assert.equal(outcome.report.phase, "declarations");
    assert.equal(outcome.report.effect, "writes-not-started"); assert(!JSON.stringify(outcome).includes("private-canary"));
  }
}));
test("wrapper symlink is rejected before any assembly writes", () => fixture(({ root, compiledRoot, temporary }) => {
  put(join(temporary, "outside"), "preserved"); symlinkSync(join(temporary, "outside"), join(compiledRoot, "handler.js"));
  const outcome = runManagedHandler(["--program", program, "--compiled-root", compiledRoot], root);
  assert.equal(outcome.exitCode, 1); assert.equal(readFileSync(join(temporary, "outside"), "utf8"), "preserved");
  assert.equal(outcome.report.effect, "writes-not-started");
}));
test("CLI rejects extra, repeated and unknown arguments without exposing them", () => {
  for (const args of [[], ["--program", program], ["--program", program, "--unknown", "private-canary"],
    ["--program", program, "--program", program], ["--program", program, "--compiled-root", "x", "extra", "private-canary"]]) {
    const outcome = runManagedHandler(args); assert.equal(outcome.exitCode, 1);
    assert.equal(outcome.report.phase, "arguments"); assert(!JSON.stringify(outcome).includes("private-canary"));
  }
});
test("dependency preparation rejects missing locked installation without publishing paths", () => fixture(({ root, temporary }) => {
  const result = runManagedHandler(["--program", program, "--destination", join(temporary, "private-canary")], root);
  assert.equal(result.exitCode, 1); assert.equal(result.report.phase, "dependencies");
  assert.equal(result.report.effect, "writes-not-started");
  assert(!JSON.stringify(result).includes("private-canary"));
}));
