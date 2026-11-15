// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.check-inputs-test
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: testing
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Prove package check input discovery follows actual commands and changed declarations without unrelated source expansion or execution.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.test.prepare-runtime-payload.wrapper
//     path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/script.sh

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { workspaceCheckInputs } from "./check-inputs.mjs";

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), "workspace-check-inputs-"));
  t.after(() => rmSync(root, { recursive: true }));
  const file = (path, value) => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), typeof value === "string" ? value : JSON.stringify(value));
  };
  const scripts = { "ledger:check": "npm run ledger:compile && node packages/ledger/check.mjs",
    "ledger:compile": "node scripts/repo/workspace-build/script.mjs --project packages/ledger/tsconfig.json --development --payload" };
  const manifest = () => file("package.json", { workspaces: ["packages/*"], scripts });
  const pkg = (name, extra = {}) => {
    file(`packages/${name}/package.json`, { name: `@renamed/${name}`, exports: { ".": "./src/index.ts" }, ...extra });
    file(`packages/${name}/src/index.ts`, "export const value = 1;\n");
  };
  pkg("ledger", { dependencies: { "@renamed/direct": "0.0.0" }, devDependencies: { "@renamed/testing": "0.0.0" } });
  pkg("direct", { dependencies: { "@renamed/transitive": "0.0.0", "driver": "1.0.0" }, devDependencies: { "@renamed/unrelated": "0.0.0" } });
  for (const name of ["transitive", "testing", "unrelated"]) pkg(name);
  file("base.json", { compilerOptions: { strict: true } });
  file("packages/ledger/tsconfig.json", { extends: "../../base.json", include: ["src"] });
  file("packages/ledger/check.mjs", 'throw new Error("MUST_NOT_EXECUTE");\n');
  file("package-lock.json", { lockfileVersion: 3, packages: {} });
  manifest();
  return { root, file, pkg, scripts, manifest, observe: () => workspaceCheckInputs(root, ["ledger:check"]) };
}

test("actual nested compiler command derives runtime and root-test closure without executing scripts", t => {
  const f = fixture(t), observed = f.observe(), record = observed.contexts["ledger:check|hooks"];
  assert.deepEqual(record.nodePackages, ["@renamed/direct", "@renamed/ledger", "@renamed/testing", "@renamed/transitive", "driver"]);
  for (const path of ["base.json", "packages/ledger/tsconfig.json", "packages/ledger/check.mjs", "packages/direct", "packages/transitive", "packages/testing"]) assert(record.references.includes(path), path);
  assert.equal(record.references.includes("packages/unrelated"), false);
  assert.equal(record.references.includes("packages/unrelated/src/index.ts"), false);
  assert(observed.discoveryInputs.includes("packages/unrelated/package.json"));
  assert.equal(readFileSync(join(f.root, "packages/ledger/check.mjs"), "utf8").includes("MUST_NOT_EXECUTE"), true);
});

test("add change and remove declarations update closure without a package-name registry", t => {
  const f = fixture(t), before = f.observe();
  f.pkg("brand-new");
  assert(f.observe().discoveryInputs.includes("packages/brand-new/package.json"));
  f.pkg("ledger", { dependencies: { "@renamed/brand-new": "0.0.0" } });
  const changed = f.observe().contexts["ledger:check|hooks"];
  assert.deepEqual(changed.nodePackages, ["@renamed/brand-new", "@renamed/ledger"]);
  assert(changed.references.includes("packages/brand-new"));
  assert.equal(changed.references.includes("packages/direct"), false);
  rmSync(join(f.root, "packages/unrelated"), { recursive: true });
  assert.equal(f.observe().discoveryInputs.includes("packages/unrelated/package.json"), false);
  assert(before.discoveryInputs.includes("packages/unrelated/package.json"));
  f.file("packages/brand-new/package.json", "PRIVATE_CANARY malformed");
  assert.throws(f.observe, error => !String(error).includes("PRIVATE_CANARY"));
});

test("npm lifecycle and ordinary declaration compiler inputs remain observed", t => {
  const f = fixture(t);
  f.file("before.mjs", "throw new Error('MUST_NOT_EXECUTE');");
  f.file("after.mjs", "throw new Error('MUST_NOT_EXECUTE');");
  f.scripts["preledger:check"] = "node before.mjs";
  f.scripts["postledger:check"] = "node after.mjs";
  f.scripts["ledger:compile"] = "tsc -p packages/ledger/tsconfig.json";
  f.manifest();
  assert(f.observe().contexts["ledger:check|hooks"].references.includes("before.mjs"));
  assert(f.observe().contexts["ledger:check|hooks"].references.includes("after.mjs"));
});

test("ignored npm hooks including nested hooks are not parsed or fingerprinted", t => {
  const f = fixture(t);
  f.scripts["preledger:check"] = "PRIVATE_CANARY unsupported shell > marker";
  f.scripts["preledger:compile"] = "PRIVATE_CANARY unsupported shell > nested-marker";
  f.manifest();
  const ignored = workspaceCheckInputs(f.root, [{ npmScript: "ledger:check", ignoreScripts: true }]);
  assert.equal(ignored.contexts["ledger:check|ignore"].ignoreScripts, true);
  assert.throws(f.observe, error => error.code === "workspace-check-command-unsupported");
  f.file(".npmrc", "ignore-scripts=true\n");
  const inherited = workspaceCheckInputs(f.root, [{ npmScript: "ledger:check", ignoreScripts: null }]);
  assert.equal(inherited.contexts["ledger:check|inherit"].ignoreScripts, true);
});

test("plain tsc cannot bypass derived aliases through inherited project configuration", t => {
  const f = fixture(t);
  f.scripts["ledger:compile"] = "tsc -p packages/ledger/tsconfig.json";
  f.manifest();
  f.file("base.json", { compilerOptions: { paths: { "PRIVATE_CANARY": ["packages/unrelated/src/index.ts"] } } });
  assert.throws(f.observe, error => error.code === "compiler-aliases-must-be-derived"
    && error.effect === "not-started" && !String(error).includes("PRIVATE_CANARY"));
});

test("unsupported commands, cycles and missing project sources fail closed with finite reasons", t => {
  const f = fixture(t);
  for (const [command, code] of [["node PRIVATE_CANARY.mjs; echo unsafe", "workspace-check-command-unsupported"],
    ["npm run ledger:check", "workspace-check-script-cycle"], ["npm run absent", "workspace-check-script-missing"]]) {
    f.scripts["ledger:check"] = command; f.manifest();
    assert.throws(f.observe, error => error.code === code && !String(error).includes("PRIVATE_CANARY"));
  }
  f.scripts["ledger:check"] = "tsc -p packages/ledger/absent.json"; f.manifest();
  assert.throws(f.observe, error => error.code === "workspace-check-source-missing");
});

test("actual stdin projector observes renamed workspaces and rejects malformed input without native values", t => {
  const f = fixture(t), script = fileURLToPath(new URL("./check-inputs.mjs", import.meta.url));
  const good = spawnSync(process.execPath, [script], { cwd: f.root, input: JSON.stringify({ scripts: ["ledger:check"] }), encoding: "utf8" });
  assert.equal(good.status, 0, good.stderr);
  assert.deepEqual(JSON.parse(good.stdout), f.observe());
  const bad = spawnSync(process.execPath, [script], { cwd: f.root, input: "PRIVATE_CANARY", encoding: "utf8" });
  assert.equal(bad.status, 1);
  assert.deepEqual(JSON.parse(bad.stdout), { error: "workspace-check-observation-unavailable" });
  assert.equal(bad.stderr, "");
});
