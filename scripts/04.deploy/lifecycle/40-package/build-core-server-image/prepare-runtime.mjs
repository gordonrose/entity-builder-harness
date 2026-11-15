#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.command.build-core-server-image.prepare-runtime
//   version: 2
//   status: draft
//   created_on: "2026-10-19"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines:
//   - architecture
//   - security
//   - sre
//   kind: script
//   purpose: Add only the generated CommonJS package shims required by the compiled Kanbien core-server payload.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.command.build-core-server-image
//     path: scripts/04.deploy/lifecycle/40-package/build-core-server-image/script.sh

import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { readProgramBuildInputs, ProgramBuildInputError } from "../../20-build/runnable-program-contract/build-inputs.mjs";
import { planRuntimePackages, writeRuntimePackages } from "../../../../repo/workspace-build/runtime-packages.mjs";

let compiledRoot;
import { WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";
const state = { phase: "arguments", location: {}, writesStarted: false };
const repository = fileURLToPath(new URL("../../../../../", import.meta.url));
try {
compiledRoot = parseCompiledRoot(process.argv.slice(2));
state.phase = "declarations";
const { inputs: { packages } } = readProgramBuildInputs(repository, { programId: "kanbien-core-server" });
writeRuntimePackages(planRuntimePackages({ compiledRoot, assetRoot: repository, packages }, state), state, { packageManifestSpace: 2 });
state.phase = "wrapper-write";
state.location = { entrypoint: "kanbien-core-server.main.js" };
writeFileSync(
  join(compiledRoot, "kanbien-core-server.main.js"),
  [
    'const { runKanbienCoreServerMain } = require("./infra/04.deploy/03.product/entrypoints/kanbien-core-server.main.js");',
    "void runKanbienCoreServerMain().catch(() => {",
    "  process.exitCode = 1;",
    "});",
    "",
  ].join("\n"),
);
} catch (cause) {
  const declared = state.phase === "declarations" && (cause instanceof WorkspaceDeclarationError || cause instanceof ProgramBuildInputError);
  if (declared) state.location = cause.location ?? {};
  console.error(JSON.stringify({ scope: "core-server-runtime-preparation", verdict: "failed", code: "runtime-preparation-boundary-failed", phase: state.phase, ...(declared ? { reason: cause.code } : {}), ...state.location, effect: state.writesStarted ? "earlier-writes-possible" : "writes-not-started" }));
  process.exitCode = 1;
}

function parseCompiledRoot(args) {
  if (args.length !== 2 || args[0] !== "--compiled-root" || args[1].length === 0) {
    throw new Error("Usage: prepare-runtime.mjs --compiled-root <compiled-output-directory>");
  }
  return args[1];
}
