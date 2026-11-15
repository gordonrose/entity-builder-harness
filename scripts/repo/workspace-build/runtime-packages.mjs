// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.runtime-packages
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.runtime-packages
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Share validated CommonJS workspace shim and declared JSON asset assembly across build and test callers.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.code.prepare-runtime-payload.assemble
//     path: scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble.mjs

import { copyFileSync, lstatSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, parse, relative, resolve, sep } from "node:path";
import { deriveWorkspaceInputs, loadWorkspaceGraph } from "./declarations.mjs";

export class RuntimePackageError extends Error {
  constructor(code) { super(code); this.name = "RuntimePackageError"; this.code = code; }
}
const fail = code => { throw new RuntimePackageError(code); };
const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const plans = new WeakSet();

export function validatePayloadPath(value) {
  if (typeof value !== "string" || !value.length || value.split("/").some(part =>
    !/^[A-Za-z0-9_@.-]+$/.test(part) || part === "." || part === "..")) fail("runtime-package-path-invalid");
}

export function rejectPayloadSymlinks(root, file) {
  const absoluteRoot = resolve(root);
  let current = parse(absoluteRoot).root;
  const parts = relative(current, absoluteRoot).split(sep).filter(Boolean).concat(file.split("/"));
  for (const part of parts) {
    current = join(current, part);
    try { if (lstatSync(current).isSymbolicLink()) fail("runtime-package-source-symlink"); }
    catch (error) {
      if (error.code === "ENOENT" || error.code === "ENOTDIR") return;
      if (error instanceof RuntimePackageError) throw error;
      fail("runtime-package-source-unreadable");
    }
  }
}

function shimOutput(key, target) {
  if (target.endsWith(".json")) return key === "." ? "index.json"
    : key.slice(2) + (key.endsWith(".json") ? "" : ".json");
  return key === "." ? "index.js" : key.slice(2) + "/index.js";
}

export function planRuntimePackages(options, state = {}) {
  state.phase = "arguments"; state.location = {}; state.writesStarted = false;
  if (!object(options) || typeof options.compiledRoot !== "string" || !options.compiledRoot.length
    || (options.assetRoot !== undefined && (typeof options.assetRoot !== "string" || !options.assetRoot.length))) fail("runtime-package-root-invalid");
  if (!object(options.packages) || !Object.keys(options.packages).length) fail("runtime-package-map-invalid");
  const compiled = resolve(options.compiledRoot), assets = resolve(options.assetRoot ?? options.compiledRoot);
  const outputs = new Set(), mappedPackages = [];
  function output(file) {
    validatePayloadPath(file);
    if ([...outputs].some(other => file === other || file.startsWith(other + "/") || other.startsWith(file + "/"))) fail("runtime-package-output-collision");
    outputs.add(file); rejectPayloadSymlinks(compiled, file);
  }
  for (const [name, exports] of Object.entries(options.packages)) {
    if (!/^(?:@[a-z0-9][a-z0-9._-]*\/)?[a-z0-9][a-z0-9._-]*$/.test(name)) fail("runtime-package-name-invalid");
    if (!object(exports) || !Object.keys(exports).length) fail("runtime-package-map-invalid");
    output(`node_modules/${name}/package.json`);
    for (const [key, target] of Object.entries(exports)) {
      if (key !== "." && (!key.startsWith("./") || key.length < 3)) fail("runtime-package-export-invalid");
      if (key !== ".") validatePayloadPath(key.slice(2));
      validatePayloadPath(target);
      if (!target.endsWith(".js") && !target.endsWith(".json")) fail("runtime-package-target-invalid");
      rejectPayloadSymlinks(target.endsWith(".json") ? assets : compiled, target);
      output(`node_modules/${name}/${shimOutput(key, target)}`);
    }
    mappedPackages.push(Object.freeze([name, Object.freeze({ ...exports })]));
  }
  const compiledInputs = mappedPackages.flatMap(([, exports]) => Object.values(exports).filter(target => !target.endsWith(".json") || assets === compiled));
  if (compiledInputs.some(input => [...outputs].some(output => input === output || input.startsWith(output + "/") || output.startsWith(input + "/")))) fail("runtime-package-source-overwrite");
  const plan = Object.freeze({ compiled, assets, mappedPackages: Object.freeze(mappedPackages),
    outputs: Object.freeze([...outputs]), compiledInputs: Object.freeze(compiledInputs) });
  plans.add(plan);
  return plan;
}

export function assertRuntimePackageInputs(plan, state = {}, { deferJsonAssets = false } = {}) {
  if (!plans.has(plan)) fail("runtime-package-plan-invalid");
  if (typeof deferJsonAssets !== "boolean") fail("runtime-package-format-invalid");
  for (const [name, exports] of plan.mappedPackages) for (const [key, target] of Object.entries(exports)) {
    if (deferJsonAssets && target.endsWith(".json")) continue;
    state.phase = "compiled-export"; state.location = { package: name, export: key, compiledExport: target };
    let source;
    try { source = lstatSync(join(target.endsWith(".json") ? plan.assets : plan.compiled, target)); }
    catch (error) { fail(error.code === "ENOENT" || error.code === "ENOTDIR" ? "runtime-package-source-missing" : "runtime-package-source-unreadable"); }
    if (!source.isFile()) fail("runtime-package-source-not-file");
  }
}

export function writeRuntimePackages(plan, state = {}, { packageManifestSpace = 0, deferJsonAssets = false } = {}) {
  if (!plans.has(plan)) fail("runtime-package-plan-invalid");
  if (![0, 2].includes(packageManifestSpace)) fail("runtime-package-format-invalid");
  // Every caller gets the no-partial-write guarantee for missing inputs, even
  // when it did not call the read-only assertion separately for a dry run.
  assertRuntimePackageInputs(plan, state, { deferJsonAssets });
  try {
    for (const [name, exports] of plan.mappedPackages) {
      const packageExports = {}, directory = join(plan.compiled, "node_modules", name);
      for (const [key, target] of Object.entries(exports)) {
        state.location = { package: name, export: key };
        const file = shimOutput(key, target), destination = join(directory, file);
        state.phase = "shim-directory"; state.writesStarted = true;
        mkdirSync(dirname(destination), { recursive: true });
        if (target.endsWith(".json")) {
          if (!deferJsonAssets) { state.phase = "asset-copy"; copyFileSync(join(plan.assets, target), destination); }
        } else {
          state.phase = "shim-write";
          const fromShim = relative(dirname(destination), join(plan.compiled, target)).split(sep).join("/");
          writeFileSync(destination, `module.exports = require(${JSON.stringify(fromShim.startsWith(".") ? fromShim : `./${fromShim}`)});\n`);
        }
        packageExports[key] = "./" + file;
      }
      state.phase = "manifest-write"; state.location = { package: name };
      writeFileSync(join(directory, "package.json"), JSON.stringify({ name, type: "commonjs", exports: packageExports }, null, packageManifestSpace) + "\n");
    }
  } catch (error) {
    if (error instanceof RuntimePackageError) throw error;
    fail("runtime-package-write-failed");
  }
}

/** Catalogue generation calls this only after compatibility/freshness succeeds.
 * Missing JSON remains an error at this final copy boundary. */
export function copyRuntimePackageAssets(plan, state = {}) {
  assertRuntimePackageInputs(plan, state);
  try {
    for (const [name, exports] of plan.mappedPackages) for (const [key, target] of Object.entries(exports)) {
      if (!target.endsWith(".json")) continue;
      const file = `node_modules/${name}/${shimOutput(key, target)}`;
      rejectPayloadSymlinks(plan.assets, target);
      rejectPayloadSymlinks(plan.compiled, file);
      state.location = { package: name, export: key };
      state.phase = "shim-directory"; state.writesStarted = true;
      mkdirSync(dirname(join(plan.compiled, file)), { recursive: true });
      state.phase = "asset-copy";
      copyFileSync(join(plan.assets, target), join(plan.compiled, file));
    }
  } catch (error) {
    if (error instanceof RuntimePackageError) throw error;
    fail("runtime-package-write-failed");
  }
}

export function prepareWorkspaceRuntime(options, state = {}) {
  state.phase = "arguments"; state.location = {}; state.writesStarted = false;
  if (!object(options)) fail("runtime-package-root-invalid");
  const graph = loadWorkspaceGraph(options.repository);
  const inputs = deriveWorkspaceInputs(graph, options.selection);
  const plan = planRuntimePackages({ compiledRoot: options.compiledRoot, assetRoot: graph.root, packages: inputs.packages }, state);
  writeRuntimePackages(plan, state, { packageManifestSpace: 2 });
  return inputs;
}
