#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.command.build-core-server-persistence-image.prepare-runtime
//   version: 4
//   status: draft
//   created_on: "2026-10-23"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.core-server-persistence
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Add CommonJS workspace shims and executable wrappers to the persistence candidate payload.
//   portability: { class: internal, targets: [] }
//   effects: [writes-files]
//   used_by:
//   - id: infra.04-deploy.03-product.image.core-server-persistence.dockerfile
//     path: infra/04.deploy/03.product/image/core-server-persistence/Dockerfile

import { fileURLToPath } from "node:url";
import { readProgramBuildInputs, ProgramBuildInputError } from "../../20-build/runnable-program-contract/build-inputs.mjs";
import { assembleRuntimePayload } from "../prepare-runtime-payload/assemble.mjs";
import { runtimeEntrypoints, wrapperSource } from "./runtime-contract.mjs";
const repository = fileURLToPath(new URL("../../../../../", import.meta.url));
import { WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";
const state = { phase: "arguments", location: {}, writesStarted: false };
try {
const compiledRoot = parseCompiledRoot(process.argv.slice(2));
state.phase = "declarations";
const { inputs: { packages } } = readProgramBuildInputs(repository, { programId: "kanbien-core-server-persistence" });
assembleRuntimePayload({ compiledRoot, assetRoot: repository, packages, packageManifestSpace: 2,
  manifest: { path: "runtime-payload.json", newline: false }, manifestBeforeWrappers: true,
  entrypoints: Object.entries(runtimeEntrypoints).map(([entry, exported]) => ({
    target: `infra/04.deploy/03.product/entrypoints/${entry}.js`, output: `${entry}.js`, source: wrapperSource(entry, exported),
  })),
}, state);
} catch (cause) {
  const declared = state.phase === "declarations" && (cause instanceof WorkspaceDeclarationError || cause instanceof ProgramBuildInputError);
  if (declared) state.location = cause.location ?? {};
  const location = state.phase === "compiled-export" ? { compiledExport: state.location.compiledExport } : state.location;
  console.error(JSON.stringify({ scope: "core-server-persistence-runtime-preparation", verdict: "failed", code: "runtime-preparation-boundary-failed", phase: state.phase, ...(declared ? { reason: cause.code } : {}), ...location, effect: state.writesStarted ? "earlier-writes-possible" : "writes-not-started" }));
  process.exitCode = 1;
}
function parseCompiledRoot(args) { if (args.length !== 2 || args[0] !== "--compiled-root" || args[1].length === 0) throw new Error("Usage: prepare-runtime.mjs --compiled-root <compiled-output-directory>"); return args[1]; }
