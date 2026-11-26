#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.build-platform-shell-image.prepare-runtime
//   version: 4
//   status: active
//   created_on: "2026-07-10"
//   updated_on: "2026-11-26"
//   layer: 04.deploy
//   domain: infra.ci-cd
//   disciplines:
//   - agentic
//   - sre
//   kind: script
//   purpose: Prepare CommonJS package shims for the platform shell image runtime payload.
//   portability:
//     class: internal
//     targets: []
//   effects:
//   - writes-files
//   used_by:
//   - id: deploy.script.build-platform-shell-image
//     path: scripts/04.deploy/legacy/kanbien-staging/build-platform-shell-image/script.sh

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { projectWorkspaceInputs } from "../../../../repo/workspace-build/project-selection.mjs";
import { WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";
import { planRuntimePackages, writeRuntimePackages } from "../../../../repo/workspace-build/runtime-packages.mjs";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "../../../../..");
const runtimeRoot = ".cache/platform-shell-image-build";
const state = { phase: "declarations", location: {}, writesStarted: false };
try {
  const { inputs } = projectWorkspaceInputs(repository, "platform/server/tsconfig.image.json", {
    unownedRootPrefixes: ["infra/04.deploy/03.product/entrypoints/"],
  });
  const plan = planRuntimePackages({ compiledRoot: resolve(runtimeRoot), assetRoot: repository,
    packages: inputs.packages }, state);
  writeRuntimePackages(plan, state, { packageManifestSpace: 2 });
  console.log(`Prepared platform shell image runtime at ${runtimeRoot}`);
} catch (cause) {
  const declared = state.phase === "declarations" && cause instanceof WorkspaceDeclarationError;
  const location = declared ? cause.location ?? {} : state.location;
  console.error(JSON.stringify({ scope: "platform-shell-runtime-preparation", verdict: "failed",
    code: "runtime-preparation-boundary-failed", phase: state.phase,
    ...(declared ? { reason: cause.code } : {}), ...location,
    effect: state.writesStarted ? "earlier-writes-possible" : "writes-not-started" }));
  process.exitCode = 1;
}
