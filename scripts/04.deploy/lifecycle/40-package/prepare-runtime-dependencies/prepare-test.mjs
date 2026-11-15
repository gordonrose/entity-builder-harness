// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.runtime-dependency-preparation
//   version: 1
//   status: draft
//   created_on: "2026-11-14"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove both copied dependency bindings, context omissions, safe reports and renamed roots with controlled installed trees.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.runtime-dependency-preparation.wrapper
//     path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/script.sh

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";
import { parse, stringify } from "yaml";
import { createDependencyPreparation } from "./prepare.mjs";
import { copyProgramFixture } from "./program-fixture.mjs";

const root = fileURLToPath(new URL("../../../../../", import.meta.url));
const home = "scripts/04.deploy/lifecycle/40-package";
const common = home + "/prepare-runtime-dependencies/prepare.mjs";
const exceptions = ["!" + home + "/prepare-runtime-dependencies/", "!" + common];
const profiles = {
  "entity-smoke": { roots: ["pg", "@aws-sdk/rds-signer"], code: "ENTITY_SMOKE_DEPENDENCIES_NOT_PREPARED" },
  "core-server-persistence": { roots: ["pg", "@aws-sdk/rds-signer", "@opentelemetry/api", "@opentelemetry/exporter-metrics-otlp-proto", "@opentelemetry/resources", "@opentelemetry/sdk-metrics"], code: "PERSISTENCE_DEPENDENCIES_NOT_PREPARED" },
};
function put(path, body) { mkdirSync(dirname(path), { recursive: true }); writeFileSync(path, body); }
function fixture(kind, body, omitted) {
  const temporary = mkdtempSync(join(tmpdir(), "runtime-dependencies-")), repository = join(temporary, "repository"), output = join(temporary, "payload/node_modules");
  const locked = {};
  function pkg(location, name, version, dependencies = {}, source = "module.exports = require('shared');") {
    put(join(repository, location, "package.json"), JSON.stringify({ name, version, main: "index.js", dependencies }));
    put(join(repository, location, "index.js"), source); locked[location] = { version };
  }
  function lock() { put(join(repository, "package-lock.json"), JSON.stringify({ lockfileVersion: 3, packages: locked })); }
  try {
    copyProgramFixture(repository, "kanbien-" + kind);
    cpSync(join(root, "node_modules/yaml"), join(repository, "node_modules/yaml"), { recursive: true });
    const dockerfile = readFileSync(join(root, "infra/04.deploy/03.product/image", kind, "Dockerfile"), "utf8");
    const context = readFileSync(join(root, "infra/04.deploy/03.product/image", kind, "Dockerfile.dockerignore"), "utf8").split(/\r?\n/).filter(line => line !== omitted);
    assert(context.includes("*"));
    // Only this extraction's exact default-deny exceptions are modelled here.
    const admitted = exceptions.every(line => context.includes(line));
    for (const [, source, target] of dockerfile.matchAll(/^COPY (scripts\/\S+\.mjs) \.\/(\S+)$/gm)) {
      if (source === common && (!admitted || omitted === "copy")) continue;
      put(join(repository, target), readFileSync(join(root, source)));
    }
    for (const name of profiles[kind].roots) pkg("node_modules/" + name, name, "1.0.0", { shared: "1" });
    pkg("node_modules/shared", "shared", "1.0.0", {}, "module.exports = 'root-v1';");
    pkg("node_modules/@aws-sdk/rds-signer/node_modules/shared", "shared", "2.0.0", {}, "module.exports = 'nested-v2';");
    pkg("node_modules/@aws-sdk/unrelated", "@aws-sdk/unrelated", "1.0.0", {}, "module.exports = 'excluded';");
    lock();
    const cli = join(repository, home, "build-" + kind + "-image/prepare-dependencies.mjs");
    const run = (args = [repository, output]) => spawnSync(process.execPath, [cli, ...args], { cwd: repository, env: { ...process.env, NODE_PATH: "" }, encoding: "utf8", timeout: 15000 });
    body({ repository, output, run, pkg, lock });
  } finally { rmSync(temporary, { recursive: true, force: true }); }
}
for (const [kind, profile] of Object.entries(profiles)) {
  test(kind + ": real copied CLI preserves report, selected closure and nested resolution", () => fixture(kind, ({ repository, output, run }) => {
    const dry = run([repository, output, "--dry-run"]); assert.equal(dry.status, 0, dry.stderr);
    const planned = JSON.parse(dry.stdout);
    assert.equal(planned.schema, "deploy/" + kind + "-dependencies/v1"); assert.equal(planned.verdict, "planned");
    assert.deepEqual(planned.roots, [...profile.roots].sort()); assert(!existsSync(output));
    const prepared = run(); assert.equal(prepared.status, 0, prepared.stderr); assert.equal(prepared.stderr, "");
    assert.deepEqual(JSON.parse(prepared.stdout), { ...planned, verdict: "prepared" });
    assert.deepEqual(planned.packages.map(pkg => pkg.name).sort(), [...profile.roots, "shared", "shared"].sort());
    assert(!existsSync(join(output, "@aws-sdk/unrelated")));
    const require = createRequire(join(output, "../probe.cjs"));
    for (const name of profile.roots) {
      assert(require.resolve(name).startsWith(output + "/"));
      assert.equal(require(name), name === "@aws-sdk/rds-signer" ? "nested-v2" : "root-v1");
    }
  }));
  test(kind + ": malformed source and CLI arguments preserve bounded safe failures", () => fixture(kind, ({ repository, output, run }) => {
    put(join(repository, "node_modules/pg/package.json"), "PRIVATE_DEPENDENCY_CANARY");
    const rejected = run(); assert.equal(rejected.status, 1); assert.equal(rejected.stdout, ""); assert(!existsSync(output));
    assert.deepEqual(JSON.parse(rejected.stderr), { verdict: "failed", code: profile.code, phase: "manifest", reason: "unreadable-or-invalid", effect: "not-started" });
    assert(!rejected.stderr.includes("PRIVATE_DEPENDENCY_CANARY")); assert(!rejected.stderr.includes(repository));
    const argumentsRejected = run([]);
    assert.deepEqual(JSON.parse(argumentsRejected.stderr), { verdict: "failed", code: profile.code, phase: "arguments", reason: "invalid", effect: "not-started" });
    assert.equal(argumentsRejected.status, 1); assert(!existsSync(output));
  }));
  for (const omitted of [...exceptions, "copy"]) test(kind + ": omitted shared input " + omitted + " prevents real preparation", () => fixture(kind, ({ output, run }) => {
    const result = run(); assert.notEqual(result.status, 0); assert(!existsSync(output));
  }, omitted));
}
test("renamed roots use the same resolver; malformed binding roots reject without writes", () => fixture("entity-smoke", ({ repository, output, pkg, lock }) => {
  pkg("node_modules/renamed-worker", "renamed-worker", "1.0.0", { shared: "1" }); lock();
  const binding = createDependencyPreparation({ roots: ["renamed-worker"], schema: "fixture/renamed/v1", code: "RENAMED_NOT_PREPARED" });
  const result = binding.prepareDependencies(repository, output);
  assert.equal(result.schema, "fixture/renamed/v1");
  assert.deepEqual(result.packages.map(pkg => pkg.name).sort(), ["renamed-worker", "shared"]);
  assert.equal(createRequire(join(output, "../probe.cjs"))("renamed-worker"), "root-v1");
  for (const roots of [[], null, [42], ["../PRIVATE_ROOT_CANARY"]]) {
    const invalid = createDependencyPreparation({ roots, schema: "fixture/invalid/v1", code: "RENAMED_NOT_PREPARED" });
    const destination = output + "-invalid";
    assert.throws(() => invalid.prepareDependencies(repository, destination), cause => cause.message === "RENAMED_NOT_PREPARED" && cause.phase === "manifest" && cause.reason === "dependency-name-invalid" && cause.effect === "not-started");
    assert(!existsSync(destination));
  }
}));

test("copied feature CLI derives added, changed and removed external roots from its program", () => fixture("entity-smoke", ({ repository, output, run, pkg, lock }) => {
  const contractPath = join(repository, "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml");
  const declaration = parse(readFileSync(contractPath, "utf8"));
  const program = declaration.runnable_programs.find(value => value.id === "kanbien-entity-smoke");
  program.approved_dependencies.push("renamed-service");
  declaration.dependency_bindings["renamed-service"] = { external_packages: ["renamed-client"] };
  pkg("node_modules/renamed-client", "renamed-client", "3.0.0", { shared: "1" }); lock();
  const save = () => writeFileSync(contractPath, stringify(declaration));
  const observe = () => { const result = run([repository, output, "--dry-run"]); assert.equal(result.status, 0, result.stderr); return JSON.parse(result.stdout); };
  save();
  assert(observe().roots.includes("renamed-client"));
  declaration.dependency_bindings["renamed-service"].external_packages = ["replacement-client"];
  pkg("node_modules/replacement-client", "replacement-client", "4.0.0", { shared: "1" }); lock(); save();
  const changed = observe();
  assert(changed.roots.includes("replacement-client"));
  assert(!changed.packages.some(value => value.name === "renamed-client"));
  program.approved_dependencies = program.approved_dependencies.filter(value => value !== "renamed-service");
  delete declaration.dependency_bindings["renamed-service"]; save();
  assert(!observe().packages.some(value => value.name.endsWith("-client")));
  assert(!existsSync(output));
  declaration.dependency_bindings.postgresql.external_packages = ["../PRIVATE_BINDING_CANARY"]; save();
  const rejected = run();
  assert.equal(rejected.status, 1);
  assert.deepEqual(JSON.parse(rejected.stderr), { verdict: "failed", code: profiles["entity-smoke"].code,
    phase: "binding", reason: "declaration-invalid", effect: "not-started" });
  assert(!rejected.stderr.includes("PRIVATE_BINDING_CANARY"));
  assert(!existsSync(output));
}));
