// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.test.persistence-fixture-runtime
//   version: 1
//   status: active
//   created_on: "2026-10-28"
//   updated_on: "2026-10-28"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Give each compiled persistence fixture a disposable independent module tree and clean it after failure or success.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.test.core-server-persistence-composition
//     path: scripts/04.deploy/lifecycle/20-build/core-server-persistence-composition/smoke-test.sh
import { cpSync, mkdtempSync, rmSync, statSync, readdirSync, readFileSync, lstatSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export function fixtureRuntime(source) {
  if (typeof source !== "string" || source.length === 0 || !statSync(source).isDirectory()) {
    throw new TypeError("A compiled fixture directory is required.");
  }
  // The owning runner's temporary parent also cleans copies after SIGKILL.
  const temporary = mkdtempSync(join(dirname(resolve(source)), "persistence-fixture-"));
  const output = join(temporary, "payload");
  const cleanup = () => rmSync(temporary, { recursive: true, force: true });
  process.once("exit", cleanup);
  try { cpSync(resolve(source), output, { recursive: true }); }
  catch (error) { cleanup(); throw error; }
  return output;
}

export function fixtureFingerprint(source) {
  const hash = createHash("sha256");
  function visit(relative) {
    const path = join(source, relative), information = lstatSync(path);
    if (information.isSymbolicLink()) throw new Error("Fixture payload symlinks are not supported.");
    hash.update(JSON.stringify([relative, information.mode & 0o777]));
    if (information.isDirectory()) for (const child of readdirSync(path).sort()) visit(join(relative, child));
    else if (information.isFile()) hash.update(readFileSync(path));
    else throw new Error("Fixture payload entry is not supported.");
  }
  visit("");
  return hash.digest("hex");
}

if (resolve(process.argv[1] ?? ".") === fileURLToPath(import.meta.url)) {
  if (process.argv[2] !== "--fingerprint" || process.argv.length !== 4) throw new Error("Usage: fixture-runtime.mjs --fingerprint <compiled-directory>");
  console.log(fixtureFingerprint(process.argv[3]));
}
