#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.command
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Bind a workspace compiler project to its discovered package owner and finite command diagnostics.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.compiler
//     path: scripts/repo/workspace-build/compile.mjs

import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { compileProject, WorkspaceCompilationError } from "./compile.mjs";
import { loadWorkspaceGraph, selectWorkspaceProject, WorkspaceDeclarationError } from "./declarations.mjs";
import { projectWorkspaceInputs } from "./project-selection.mjs";

const repository = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");

export function workspaceCompilerOptions(args, root = repository) {
  const invalid = () => { throw new WorkspaceCompilationError("compiler-arguments-invalid"); };
  if (!Array.isArray(args)) invalid();
  const seen = new Set(), options = { root, compilerArguments: [] };
  let development = false, projectRoots = false, generatedJsonAssets = false, unownedRootPrefix;
  for (let index = 0; index < args.length; index++) {
    const flag = args[index];
    if (seen.has(flag)) invalid();
    seen.add(flag);
    if (flag === "--development") development = true;
    else if (flag === "--project-roots") projectRoots = true;
    else if (flag === "--generated-json-assets") generatedJsonAssets = true;
    else if (flag === "--payload") options.payload = true;
    else if (["--project", "--outDir", "--incremental", "--unowned-root-prefix"].includes(flag)) {
      const value = args[++index];
      if (typeof value !== "string" || !value || value.startsWith("--") || value.includes("\0")) invalid();
      if (flag === "--project") options.project = value;
      else if (flag === "--unowned-root-prefix") unownedRootPrefix = value;
      else options.compilerArguments.push(flag, value);
    } else invalid();
  }
  if (!options.project) invalid();
  if ((projectRoots && development) || ((unownedRootPrefix || generatedJsonAssets) && !projectRoots)) invalid();
  if (projectRoots) {
    options.selection = projectWorkspaceInputs(root, options.project, {
      unownedRootPrefixes: unownedRootPrefix ? [unownedRootPrefix] : [],
      allowMissingJsonAssets: generatedJsonAssets,
    }).selection;
    return options;
  }
  let owner;
  try { owner = selectWorkspaceProject(loadWorkspaceGraph(root), options.project); }
  catch (error) {
    if (error instanceof WorkspaceDeclarationError && error.code === "workspace-project-owner-missing") {
      throw new WorkspaceCompilationError("compiler-workspace-owner-missing");
    }
    throw error;
  }
  options.selection = { roots: [owner], includeRootDevDependencies: development };
  return options;
}

export function runWorkspaceCompiler(args, { root = repository, compile = compileProject } = {}) {
  try {
    compile(workspaceCompilerOptions(args, root));
    return { exitCode: 0 };
  } catch (error) {
    const known = error instanceof WorkspaceCompilationError || error instanceof WorkspaceDeclarationError;
    return { exitCode: known && Number.isInteger(error.exitCode) && error.exitCode > 0 ? error.exitCode : 1,
      diagnostic: { code: known ? error.code : "compiler-boundary-failed",
        effect: known ? error.effect ?? "not-started" : "unknown",
        diagnosticCodes: known ? error.diagnosticCodes ?? [] : [],
        diagnosticsTruncated: known ? error.diagnosticsTruncated ?? false : false } };
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const outcome = runWorkspaceCompiler(process.argv.slice(2));
  if (outcome.diagnostic) process.stderr.write(`${JSON.stringify(outcome.diagnostic)}\n`);
  process.exitCode = outcome.exitCode;
}
