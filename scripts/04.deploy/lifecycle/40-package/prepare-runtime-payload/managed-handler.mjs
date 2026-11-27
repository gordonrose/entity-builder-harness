// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.code.prepare-runtime-payload.managed-handler
//   version: 1
//   status: draft
//   created_on: "2026-11-27"
//   updated_on: "2026-11-27"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Bind one declared managed handler to the existing payload and installed-dependency assemblers.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.image.scheduling-lambda
//     path: infra/04.deploy/03.product/image/scheduling-lambda/Dockerfile

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readProgramBuildInputs, ProgramBuildInputError } from "../../20-build/runnable-program-contract/build-inputs.mjs";
import { WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";
import { assembleRuntimePayload } from "./assemble.mjs";
import { createDependencyPreparation } from "../prepare-runtime-dependencies/prepare.mjs";

const repository = fileURLToPath(new URL("../../../../../", import.meta.url));

export function prepareManagedHandler({ root = repository, programId, compiledRoot, destination, dryRun = false }, state = {}) {
  state.phase = "declarations"; state.location = {}; state.writesStarted = false;
  const selected = readProgramBuildInputs(root, { programId });
  const entry = selected.runtimeEntry;
  if (entry.executionKind !== "managed-handler") throw new ProgramBuildInputError("program-build-handler-invalid");
  if (destination !== undefined) {
    if (compiledRoot !== undefined) throw new ProgramBuildInputError("program-build-arguments-invalid");
    state.phase = "dependencies";
    return createDependencyPreparation({ roots: Object.keys(selected.externalOwners).sort(),
      schema: "deploy/managed-handler-dependencies/v1", code: "MANAGED_HANDLER_DEPENDENCIES_NOT_PREPARED" })
      .prepareDependencies(root, destination, dryRun);
  }
  const source = '"use strict";\nconst selected = require(' + JSON.stringify("./" + entry.compiled) + ');\n'
    + 'const handler = selected[' + JSON.stringify(entry.handlerExport) + '];\n'
    + 'if (typeof handler !== "function") throw new Error("MANAGED_HANDLER_EXPORT_INVALID");\n'
    + 'exports[' + JSON.stringify(entry.handlerExport) + '] = handler;\n';
  assembleRuntimePayload({ compiledRoot, assetRoot: root, packages: selected.inputs.packages, dryRun,
    manifest: { path: "runtime-payload.json", newline: true },
    entrypoints: [{ target: entry.compiled, output: entry.output, source }] }, state);
  return { schema: "deploy/managed-handler-payload/v1", verdict: dryRun ? "planned" : "prepared",
    program_id: selected.programId, handler: entry.output.replace(/\.(?:js|cjs|mjs)$/, "") + "." + entry.handlerExport };
}

export function runManagedHandler(args, root = repository) {
  const state = { phase: "arguments", location: {}, writesStarted: false };
  try {
    if (!Array.isArray(args) || args.length !== 4) throw new Error("arguments");
    const values = {};
    for (let index = 0; index < args.length; index += 2) {
      const key = { "--program": "programId", "--compiled-root": "compiledRoot", "--destination": "destination" }[args[index]];
      if (!key || Object.hasOwn(values, key) || typeof args[index + 1] !== "string" || !args[index + 1] || args[index + 1].startsWith("--")) throw new Error("arguments");
      values[key] = args[index + 1];
    }
    if (!values.programId || (!values.compiledRoot && !values.destination)) throw new Error("arguments");
    return { exitCode: 0, report: prepareManagedHandler({ root, ...values }, state) };
  } catch (error) {
    const declared = error instanceof ProgramBuildInputError || error instanceof WorkspaceDeclarationError;
    return { exitCode: 1, report: { schema: "deploy/managed-handler-preparation/v1", verdict: "failed",
      code: "managed-handler-preparation-failed", phase: state.phase,
      ...(declared ? { reason: error.code } : {}), effect: state.writesStarted || (state.phase === "dependencies" && error?.effect === "earlier-writes-possible") ? "earlier-writes-possible" : "writes-not-started" } };
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const result = runManagedHandler(process.argv.slice(2));
  (result.exitCode ? process.stderr : process.stdout).write(JSON.stringify(result.report) + "\n");
  process.exitCode = result.exitCode;
}
