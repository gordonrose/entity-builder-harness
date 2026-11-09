// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.entity-smoke.dependencies
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove dependency preparation preserves installed versions, excludes unrelated packages and rejects unsafe or incomplete inputs before copying.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.entity-smoke.composition.wrapper
//     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh

import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, existsSync, symlinkSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dependencyClosure, prepareDependencies } from "./prepare-dependencies.mjs";

const fixture = mkdtempSync(join(tmpdir(), "kanbien-entity-smoke-dependencies-"));
assert(fixture.startsWith(join(tmpdir(), "kanbien-entity-smoke-dependencies-")));
try {
  const source = join(fixture, "source"), output = join(fixture, "payload/node_modules"), locked = {};
  function pkg(location, name, version, attributes = {}, body = "module.exports = {};") {
    const path = join(source, location);
    mkdirSync(path, { recursive: true });
    writeFileSync(join(path, "package.json"), JSON.stringify({ name, version, main: "index.js", ...attributes }));
    writeFileSync(join(path, "index.js"), body);
    locked[location] = { version };
  }
  function lock() { writeFileSync(join(source, "package-lock.json"), JSON.stringify({ lockfileVersion: 3, packages: locked })); }
  pkg("node_modules/pg", "pg", "1.0.0", { dependencies: { shared: "1", "absent-optional": "1" }, optionalDependencies: { "absent-optional": "1", "present-optional": "1" }, peerDependencies: { "absent-peer": "1" }, peerDependenciesMeta: { "absent-peer": { optional: true } } }, "module.exports = { version: require('shared'), optional: require('present-optional') };");
  pkg("node_modules/@aws-sdk/rds-signer", "@aws-sdk/rds-signer", "1.0.0", { dependencies: { shared: "2" } }, "module.exports = require('shared');");
  pkg("node_modules/shared", "shared", "1.0.0", {}, "module.exports = 'root-v1';");
  pkg("node_modules/@aws-sdk/rds-signer/node_modules/shared", "shared", "2.0.0", {}, "module.exports = 'nested-v2';");
  pkg("node_modules/present-optional", "present-optional", "1.0.0", {}, "module.exports = 'optional';");
  pkg("node_modules/@aws-sdk/unrelated", "@aws-sdk/unrelated", "1.0.0");
  lock();
  const expected = ["@aws-sdk/rds-signer", "shared", "pg", "present-optional", "shared"].sort();
  assert.deepEqual(dependencyClosure(source).map(item => item.name).sort(), expected);
  const dry = prepareDependencies(source, output, true);
  assert.equal(dry.verdict, "planned"); assert.equal(existsSync(output), false);
  const result = prepareDependencies(source, output);
  assert.equal(result.verdict, "prepared");
  assert.equal(existsSync(join(output, "@aws-sdk/unrelated")), false);
  const requireOutput = createRequire(join(fixture, "probe.cjs"));
  assert.deepEqual(requireOutput(join(output, "pg")), { version: "root-v1", optional: "optional" });
  assert.equal(requireOutput(join(output, "@aws-sdk/rds-signer")), "nested-v2");
  assert.throws(() => prepareDependencies(source, output), cause => cause.phase === "destination" && cause.effect === "not-started");

  const pgManifest = join(source, "node_modules/pg/package.json"), original = readFileSync(pgManifest, "utf8");
  const failedOutput = join(fixture, "failed-output");
  function rejected(phase, reason) {
    assert.throws(() => prepareDependencies(source, failedOutput), cause => cause.phase === phase && cause.reason === reason && cause.effect === "not-started");
    assert.equal(existsSync(failedOutput), false);
  }
  const missing = JSON.parse(original); missing.dependencies["required-missing"] = "1";
  writeFileSync(pgManifest, JSON.stringify(missing)); rejected("resolution", "required-dependency-missing");
  writeFileSync(pgManifest, "not-json-sensitive-canary"); rejected("manifest", "unreadable-or-invalid");
  const cli = spawnSync(process.execPath, [fileURLToPath(new URL("./prepare-dependencies.mjs", import.meta.url)), source, failedOutput], { encoding: "utf8" });
  assert.equal(cli.status, 1); assert.equal(cli.stdout, "");
  assert.deepEqual(JSON.parse(cli.stderr), { verdict: "failed", code: "ENTITY_SMOKE_DEPENDENCIES_NOT_PREPARED", phase: "manifest", reason: "unreadable-or-invalid", effect: "not-started" });
  assert.equal(cli.stderr.includes("sensitive-canary"), false); assert.equal(cli.stderr.includes(fixture), false);
  writeFileSync(pgManifest, original);
  locked["node_modules/pg"].version = "9.0.0"; lock(); rejected("manifest", "installed-lock-mismatch");
  locked["node_modules/pg"].version = "1.0.0"; lock();
  symlinkSync(join(output, "shared/index.js"), join(source, "node_modules/pg/escaped.js"));
  rejected("source", "symlink-not-permitted");
  rmSync(join(source, "node_modules/pg/escaped.js"));
  symlinkSync(join(output, "shared"), join(source, "node_modules/pg/node_modules"), "dir");
  rejected("source", "symlink-not-permitted");
  rmSync(join(source, "node_modules/pg/node_modules"));
  symlinkSync(join(fixture, "missing-package"), join(source, "node_modules/absent-optional"), "dir");
  rejected("source", "symlink-not-permitted");
  rmSync(join(source, "node_modules/absent-optional"));
  symlinkSync(join(fixture, "missing-destination"), failedOutput, "dir");
  rejectedDestination(failedOutput);
  rmSync(failedOutput);
  rejectedDestination(source); rejectedDestination(join(source, "new-output"));
  function rejectedDestination(destination) { assert.throws(() => prepareDependencies(source, destination), cause => cause.phase === "destination" && cause.effect === "not-started"); }
  console.log(JSON.stringify({ verdict: "passed", scope: "entity-smoke-dependency-preparation", cases: ["selected-closure", "installed-optionals", "optional-peer-absence", "nested-version-resolution", "unrelated-sdk-excluded", "dry-run-no-write", "required-missing", "safe-cli-diagnostic", "lock-mismatch", "file-symlink", "nested-tree-symlink", "dangling-optional-symlink", "dangling-destination-symlink", "destination-overlap"] }));
} finally { rmSync(fixture, { recursive: true, force: true }); }
