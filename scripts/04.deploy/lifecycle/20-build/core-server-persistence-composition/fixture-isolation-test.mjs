// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.persistence-fixture-isolation
//   version: 1
//   status: active
//   created_on: "2026-10-28"
//   updated_on: "2026-10-28"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Prove copied fixture modules do not contaminate source or siblings and are removed after child failure.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
const source = mkdtempSync(join(tmpdir(), "fixture-isolation-source-"));
const helper = new URL("./fixture-runtime.mjs", import.meta.url).href;
try {
  writeFileSync(join(source, "module.cjs"), "module.exports = 'original';\n");
  const original = readFileSync(join(source, "module.cjs"));
  for (const order of [["configuration", "observability"], ["observability", "configuration"], ["configuration", "configuration"], ["failure", "observability"]]) {
    for (const name of order) {
      const code = `import { fixtureRuntime } from ${JSON.stringify(helper)};
import { readFileSync, writeFileSync } from 'node:fs';
const payload = fixtureRuntime(${JSON.stringify(source)});
console.log(payload);
if (readFileSync(payload + '/module.cjs', 'utf8') !== "module.exports = 'original';\\n") throw Error('contaminated');
writeFileSync(payload + '/module.cjs', ${JSON.stringify(name)});
if (${JSON.stringify(name)} === 'failure') throw Error('synthetic fixture failure');`;
      const result = spawnSync(process.execPath, ["--input-type=module", "-e", code], { encoding: "utf8" });
      assert.equal(result.status, name === "failure" ? 1 : 0, result.stderr);
      const payload = result.stdout.trim();
      assert.ok(payload.length > 0);
      assert.equal(existsSync(payload), false, "Child exit must clean its disposable payload even after an uncaught failure.");
      assert.deepEqual(readFileSync(join(source, "module.cjs")), original, "Injection must never modify the compiled baseline.");
    }
  }
} finally { rmSync(source, { recursive: true, force: true }); }
console.log("Persistence fixture isolation passed.");
