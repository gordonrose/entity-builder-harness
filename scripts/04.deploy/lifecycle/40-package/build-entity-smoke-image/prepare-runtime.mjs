// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.entity-smoke.prepare-runtime
//   version: 2
//   status: draft
//   created_on: "2026-11-07"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Assemble only the isolated feature program exports and safe generated package wrappers.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: infra.04-deploy.entity-smoke.image.dockerfile
//     path: infra/04.deploy/03.product/image/entity-smoke/Dockerfile

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readProgramBuildInputs, ProgramBuildInputError } from "../../20-build/runnable-program-contract/build-inputs.mjs";
import { assembleRuntimePayload } from "../prepare-runtime-payload/assemble.mjs";
const repository = fileURLToPath(new URL("../../../../../", import.meta.url));
import { WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";
const state = { phase: "arguments", writesStarted: false, location: {} };
try {
  const args = process.argv.slice(2);
  if (args.length < 2 || args[0] !== "--compiled-root" || !args[1] || args.slice(2).some(arg => arg !== "--dry-run")) throw new Error("arguments");
  const compiled = resolve(args[1]), dry = args.includes("--dry-run");
  const entrypoints = {
    "kanbien-entity-smoke.main": ["runEntitySmokeMain", "startup"],
    "kanbien-entity-smoke-migration.main": ["runEntitySmokeMigration", "migration"],
    "kanbien-entity-smoke-administration.main": ["runEntitySmokeAdministration", "administration"],
    "kanbien-entity-smoke-verifier.main": ["runEntitySmokeVerifier", "verification"],
    "kanbien-entity-smoke-database-proof.main": ["runEntitySmokeDatabaseProof", "verification"],
  };
  state.phase = "declarations";
const { inputs: { packages } } = readProgramBuildInputs(repository, { programId: "kanbien-entity-smoke" });
  assembleRuntimePayload({ compiledRoot: compiled, assetRoot: repository, packages, dryRun: dry,
    manifest: { path: "entity-smoke-payload.json", newline: true },
    entrypoints: Object.entries(entrypoints).map(([entry, [exported, operation]]) => {
      const target = "./infra/04.deploy/03.product/entrypoints/" + entry + ".js";
      return { target: target.slice(2), output: entry + ".js",
        source: "const entry = require(" + JSON.stringify(target) + ");\nmodule.exports = entry;\nif (require.main === module) void entry." + exported + "().catch(cause => { require('./infra/04.deploy/03.product/entrypoints/entity-smoke/diagnostics.js').reportEntitySmokeFailure(" + JSON.stringify(operation) + ", 'unknown', cause); process.exitCode = 1; });\n" };
    }),
  }, state);
  console.log(JSON.stringify({ scope: "entity-smoke-runtime-preparation", verdict: dry ? "planned" : "prepared" }));
} catch (cause) {
  const declared = state.phase === "declarations" && (cause instanceof WorkspaceDeclarationError || cause instanceof ProgramBuildInputError);
  if (declared) state.location = cause.location ?? {};
  const { compiledExport, ...location } = state.location;
  if (location.entrypoint) location.entrypoint = location.entrypoint.replace(/\.js$/, "");
  console.error(JSON.stringify({ scope: "entity-smoke-runtime-preparation", verdict: "failed", code: "runtime-preparation-boundary-failed", phase: state.phase, ...(declared ? { reason: cause.code } : {}), ...location, effect: state.writesStarted ? "earlier-writes-possible" : "writes-not-started" }));
  process.exitCode = 1;
}

