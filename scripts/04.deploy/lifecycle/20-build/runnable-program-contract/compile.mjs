#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.runnable-program.compile
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Compile a declared runnable program through the common workspace compiler and preserve finite failure outcomes.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: deploy.runnable-program.build-inputs
//     path: scripts/04.deploy/lifecycle/20-build/runnable-program-contract/build-inputs.mjs

import { resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { readProgramBuildInputs, ProgramBuildInputError } from "./build-inputs.mjs";
import { compileProject, WorkspaceCompilationError } from "../../../../repo/workspace-build/compile.mjs";
import { WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";

const repository = fileURLToPath(new URL("../../../../../", import.meta.url));
export function compileProgram(args, { root = repository, compile = compileProject } = {}) {
  try {
    if (!Array.isArray(args) || args.length % 2) throw new ProgramBuildInputError("program-build-arguments-invalid");
    const options = {}, compilerArguments = [];
    for (let index = 0; index < args.length; index += 2) {
      const flag = args[index], value = args[index + 1];
      if (!["--program", "--outDir", "--incremental"].includes(flag) || Object.hasOwn(options, flag)
        || typeof value !== "string" || !value || value.startsWith("--") || value.includes("\0")) throw new ProgramBuildInputError("program-build-arguments-invalid");
      options[flag] = value;
      if (flag !== "--program") compilerArguments.push(flag, value);
    }
    const { project, selection } = readProgramBuildInputs(root, { programId: options["--program"] });
    compile({ root, project, selection, payload: true, compilerArguments });
    return { exitCode: 0 };
  } catch (error) {
    const known = error instanceof ProgramBuildInputError || error instanceof WorkspaceCompilationError || error instanceof WorkspaceDeclarationError;
    return { exitCode: known && Number.isInteger(error.exitCode) && error.exitCode > 0 ? error.exitCode : 1,
      diagnostic: { code: known ? error.code : "program-build-boundary-failed", effect: known ? error.effect ?? "not-started" : "unknown",
        diagnosticCodes: known ? error.diagnosticCodes ?? [] : [], diagnosticsTruncated: known ? error.diagnosticsTruncated ?? false : false } };
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outcome = compileProgram(process.argv.slice(2));
  if (outcome.diagnostic) process.stderr.write(`${JSON.stringify(outcome.diagnostic)}\n`);
  process.exitCode = outcome.exitCode;
}
