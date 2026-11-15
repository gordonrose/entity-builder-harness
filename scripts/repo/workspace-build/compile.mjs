// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.compiler
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Compile an explicitly selected workspace closure through the existing TypeScript compiler without handwritten aliases.
//   portability: {class: source-only, targets: []}
//   effects: [read-only, writes-files]
//   used_by:
//   - id: repo.workspace-build.compiler-test
//     path: scripts/repo/workspace-build/compile-test.mjs

import { lstatSync, mkdtempSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, isAbsolute, join, relative, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { loadWorkspaceGraph, deriveWorkspaceInputs, WorkspaceDeclarationError } from "./declarations.mjs";

export class WorkspaceCompilationError extends Error {
  constructor(code, effect = "not-started", exitCode, diagnosticCodes = []) {
    super(code);
    this.name = "WorkspaceCompilationError";
    this.code = code;
    this.effect = effect;
    if (exitCode !== undefined) this.exitCode = exitCode;
    const codes = [...new Set(diagnosticCodes.filter(value => Number.isInteger(value) && value > 0))].sort((a, b) => a - b);
    this.diagnosticCodes = codes.slice(0, 32);
    this.diagnosticsTruncated = codes.length > 32;
  }
}

function reject(code) { throw new WorkspaceCompilationError(code); }
function contained(root, target) {
  const distance = relative(root, target);
  return distance !== ".." && !distance.startsWith("../") && !isAbsolute(distance);
}

function compilerDiagnosticCodes(child) {
  const codes = [];
  for (const text of [child.stdout, child.stderr]) {
    if (typeof text !== "string") continue;
    for (const line of text.split(/\r?\n/)) {
      const match = /^(?:.+\(\d+,\d+\): )?(?:error|warning) TS(\d{1,5}):/.exec(line);
      if (match) codes.push(Number(match[1]));
    }
  }
  return codes;
}

function checkedArguments(root, values) {
  if (!Array.isArray(values) || values.length % 2) reject("compiler-arguments-invalid");
  const seen = new Set(), checked = [];
  for (let index = 0; index < values.length; index += 2) {
    const flag = values[index], value = values[index + 1];
    if (!new Set(["--outDir", "--incremental"]).has(flag) || seen.has(flag) ||
        typeof value !== "string" || !value || value.includes("\0")) reject("compiler-arguments-invalid");
    if (flag === "--incremental" && !["true", "false"].includes(value)) reject("compiler-arguments-invalid");
    seen.add(flag);
    checked.push(flag, flag === "--outDir" ? resolve(root, value) : value);
  }
  return checked;
}

/** Derive aliases, then invoke the installed compiler once. Output ownership and
 * fresh-directory publication remain with the caller; this operation never
 * recursively removes a configured output directory. Native compiler output is
 * not returned as a diagnostic. Injection is per call for controlled fixtures. */
export function compileProject(options = {}, { runCompiler = spawnSync } = {}) {
  let temporary, invoked = false, failure, result;
  try {
    if (!options || typeof options !== "object" || typeof options.root !== "string" ||
        typeof options.project !== "string" || !options.project || options.project.includes("\0") ||
        (options.payload !== undefined && typeof options.payload !== "boolean")) reject("compiler-arguments-invalid");
    const root = resolve(options.root), project = resolve(root, options.project);
    if (!contained(root, project) || !project.endsWith(".json") || !lstatSync(project).isFile() ||
        realpathSync(project) !== project) reject("compiler-project-invalid");
    const compilerArguments = checkedArguments(root, options.compilerArguments ?? []);
    const inputs = deriveWorkspaceInputs(loadWorkspaceGraph(root), options.selection);
    const require = createRequire(join(root, "package.json"));
    const ts = require("typescript");
    const compiler = join(dirname(require.resolve("typescript/package.json")), "bin/tsc");
    const configFailures = [];
    const config = ts.getParsedCommandLineOfConfigFile(project, {}, {
      ...ts.sys, onUnRecoverableConfigFileDiagnostic(diagnostic) { configFailures.push(diagnostic.code); },
    });
    if (configFailures.length || !config || config.errors.length) throw new WorkspaceCompilationError(
      "compiler-project-invalid", "not-started", undefined, [...configFailures, ...(config?.errors ?? []).map(item => item.code)]);
    if (config.projectReferences?.length) reject("compiler-project-references-unsupported");
    if (config.options.paths && Object.keys(config.options.paths).length) reject("compiler-aliases-must-be-derived");
    const generated = {
      extends: project,
      compilerOptions: {
        baseUrl: root, paths: inputs.compilerPaths,
        // Default type lookup follows the config's location, not the process
        // cwd. Preserve the original effective roots before relocating it.
        typeRoots: ts.getEffectiveTypeRoots(config.options, ts.sys) ?? [],
      },
    };
    if (options.payload) {
      generated.files = [...new Set([...config.fileNames, ...inputs.sourceFiles.map(file => resolve(root, file))])].sort();
      generated.include = [];
    }
    temporary = mkdtempSync(join(tmpdir(), "workspace-compiler-"));
    const configuration = join(temporary, "tsconfig.json");
    writeFileSync(configuration, JSON.stringify(generated), { flag: "wx", mode: 0o600 });
    invoked = true;
    const child = runCompiler(process.execPath, [compiler, "--project", configuration, "--pretty", "false", ...compilerArguments], {
      cwd: root, encoding: "utf8", stdio: "pipe",
    });
    if (child.error) throw new WorkspaceCompilationError("compiler-process-unavailable", "outputs-possible");
    if (child.signal || child.status === null) throw new WorkspaceCompilationError("compiler-interrupted", "outputs-possible");
    if (!Number.isInteger(child.status) || child.status < 0) throw new WorkspaceCompilationError("compiler-result-invalid", "outputs-possible");
    if (child.status !== 0) throw new WorkspaceCompilationError("compiler-failed", "outputs-possible", child.status, compilerDiagnosticCodes(child));
    result = { status: 0, inputs };
  } catch (cause) {
    failure = cause instanceof WorkspaceCompilationError || cause instanceof WorkspaceDeclarationError ? cause :
      new WorkspaceCompilationError(invoked ? "compiler-process-unavailable" : "compiler-preparation-unavailable",
        invoked ? "outputs-possible" : "not-started");
  } finally {
    if (temporary) {
      try { rmSync(temporary, { recursive: true }); }
      catch { failure ??= new WorkspaceCompilationError("compiler-temporary-cleanup-failed", invoked ? "outputs-possible" : "not-started"); }
    }
  }
  if (failure) throw failure;
  return result;
}
