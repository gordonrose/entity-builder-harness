// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.code.prepare-runtime-payload.assemble
//   version: 2
//   status: draft
//   created_on: "2026-11-14"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Assemble validated CommonJS mappings and workload-owned wrappers through one filesystem implementation.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.command.build-core-server-persistence-image.prepare-runtime
//     path: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/prepare-runtime.mjs
//   - id: deploy.script.entity-smoke.prepare-runtime
//     path: scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/prepare-runtime.mjs

import { existsSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { assertRuntimePackageInputs, planRuntimePackages, rejectPayloadSymlinks as rejectSymlinks,
  validatePayloadPath as validatePath, writeRuntimePackages } from "../../../../repo/workspace-build/runtime-packages.mjs";

// The CLI owns the state object so a thrown filesystem operation preserves the
// last established stage. It never contains native exceptions or supplied roots.
export function assembleRuntimePayload({ compiledRoot, assetRoot = compiledRoot, packages, entrypoints, manifest,
  dryRun = false, packageManifestSpace = 0, manifestBeforeWrappers = false }, state) {
  state.phase = "arguments"; state.location = {}; state.writesStarted = false;
  if (typeof compiledRoot !== "string" || !compiledRoot.length || typeof assetRoot !== "string" || !assetRoot.length) throw new Error("root");
  const compiled = resolve(compiledRoot);
  if (!entrypoints.length || typeof dryRun !== "boolean"
    || ![0, 2].includes(packageManifestSpace) || typeof manifestBeforeWrappers !== "boolean") throw new Error("mapping");
  const packagePlan = planRuntimePackages({ compiledRoot, assetRoot, packages }, state);
  const { mappedPackages } = packagePlan;
  const destinations = new Set();
  function output(file) {
    validatePath(file);
    if (destinations.has(file) || [...destinations].some(other => file.startsWith(other + "/") || other.startsWith(file + "/"))) throw new Error("collision");
    destinations.add(file); rejectSymlinks(compiled, file);
  }
  packagePlan.outputs.forEach(output);
  for (const entry of entrypoints) {
    validatePath(entry.target); validatePath(entry.output);
    if (typeof entry.source !== "string" || !entry.source.length) throw new Error("wrapper");
    rejectSymlinks(compiled, entry.target); output(entry.output);
  }
  output(manifest.path);
  if (typeof manifest.newline !== "boolean") throw new Error("manifest");
  const compiledInputs = [...entrypoints.map(entry => entry.target), ...packagePlan.compiledInputs];
  if (compiledInputs.some(input => [...destinations].some(output => input === output || input.startsWith(output + "/") || output.startsWith(input + "/")))) throw new Error("source-overwrite");
  for (const entry of entrypoints) {
    state.phase = "compiled-entrypoint"; state.location = { entrypoint: entry.output };
    if (!existsSync(join(compiled, entry.target))) throw new Error("missing");
  }
  assertRuntimePackageInputs(packagePlan, state);
  if (dryRun) return;
  writeRuntimePackages(packagePlan, state, { packageManifestSpace });
  const writeManifest = () => {
    state.phase = "payload-manifest-write"; state.location = {};
    const required_imports = mappedPackages.flatMap(([name, exports]) => Object.keys(exports).map(key => name + (key === "." ? "" : key.slice(1))));
    writeFileSync(join(compiled, manifest.path), JSON.stringify({ required_imports }) + (manifest.newline ? "\n" : ""));
  };
  if (manifestBeforeWrappers) writeManifest();
  for (const entry of entrypoints) {
    state.phase = "wrapper-write"; state.location = { entrypoint: entry.output };
    writeFileSync(join(compiled, entry.output), entry.source);
  }
  if (!manifestBeforeWrappers) writeManifest();
}
