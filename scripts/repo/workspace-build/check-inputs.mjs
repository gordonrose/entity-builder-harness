#!/usr/bin/env node
// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.check-inputs
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.declarations
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Derive existing package-check source and installation inputs from supported npm compiler commands without executing them.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: repo.compiler.check-selection
//     path: scripts/repo/check-selection/script.py

import { readFileSync, realpathSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";
import { deriveWorkspaceInputs, loadWorkspaceGraph, selectWorkspaceProject, WorkspaceDeclarationError } from "./declarations.mjs";
import { workspaceCompilerOptions } from "./script.mjs";
import { WorkspaceCompilationError } from "./compile.mjs";

export class WorkspaceCheckInputError extends Error {
  constructor(code) { super(code); this.name = "WorkspaceCheckInputError"; this.code = code; }
}
const fail = code => { throw new WorkspaceCheckInputError(code); };
const scriptName = value => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9:._-]*$/.test(value);
const safePath = value => typeof value === "string" && value.split("/").every(part => /^[A-Za-z0-9_@.+-]+$/.test(part) && part !== "." && part !== "..");
export const checkContextKey = ({ npmScript, ignoreScripts }) => `${npmScript}|${ignoreScripts === null ? "inherit" : ignoreScripts ? "ignore" : "hooks"}`;

export function workspaceCheckInputs(repository, scripts) {
  if (!Array.isArray(scripts) || !scripts.length) fail("workspace-check-selection-invalid");
  const selections = scripts.map(value => typeof value === "string" ? { npmScript: value, ignoreScripts: false } : value);
  if (selections.some(value => !value || typeof value !== "object" || Array.isArray(value)
    || Object.keys(value).sort().join() !== "ignoreScripts,npmScript" || !scriptName(value.npmScript)
    || value.ignoreScripts !== null && typeof value.ignoreScripts !== "boolean")
    || new Set(selections.map(checkContextKey)).size !== selections.length) fail("workspace-check-selection-invalid");
  const graph = loadWorkspaceGraph(repository), manifest = JSON.parse(readFileSync(resolve(graph.root, "package.json"), "utf8"));
  if (!manifest.scripts || typeof manifest.scripts !== "object" || Array.isArray(manifest.scripts)) fail("workspace-check-scripts-missing");
  const discoveryInputs = [...new Set([...graph.manifestPaths, ...[...graph.packages.values()].map(record => record.manifestPath)])].sort();
  const contexts = {};
  function checkedPath(path) {
    if (!safePath(path)) fail("workspace-check-path-invalid");
    const absolute = resolve(graph.root, path);
    try { if (realpathSync(absolute) !== absolute) fail("workspace-check-source-symlink"); }
    catch (error) { if (error instanceof WorkspaceCheckInputError) throw error; fail("workspace-check-source-missing"); }
    return absolute;
  }
  let inheritedIgnore;
  if (selections.some(value => value.ignoreScripts === null)) {
    const result = spawnSync("npm", ["config", "get", "ignore-scripts"], { cwd: graph.root, encoding: "utf8", timeout: 10000 });
    if (result.error || result.status !== 0 || !["true", "false"].includes(result.stdout.trim())) fail("workspace-check-npm-config-unavailable");
    inheritedIgnore = result.stdout.trim() === "true";
  }
  for (const selected of selections) {
    const ignoreScripts = selected.ignoreScripts ?? inheritedIgnore;
    const references = new Set(["package.json", "package-lock.json", "scripts/repo/workspace-build"]), packages = new Set(), pending = new Set();
    let projects = 0;
    function project(path, selection) {
      const absolute = checkedPath(path), inputs = deriveWorkspaceInputs(graph, selection);
      const host = { ...ts.sys, readFile(file) {
        const relativeFile = relative(graph.root, file).split(sep).join("/");
        checkedPath(relativeFile); references.add(relativeFile); return ts.sys.readFile(file);
      } };
      const config = ts.readConfigFile(absolute, host.readFile);
      if (config.error) fail("workspace-check-project-invalid");
      const parsed = ts.parseJsonConfigFileContent(config.config, host, dirname(absolute));
      if (parsed.errors.length || parsed.projectReferences?.length) fail("workspace-check-project-invalid");
      if (parsed.options.paths && Object.keys(parsed.options.paths).length) throw new WorkspaceCompilationError("compiler-aliases-must-be-derived");
      for (const file of parsed.fileNames) {
        const path = relative(graph.root, file).split(sep).join("/");
        checkedPath(path); references.add(path);
      }
      for (const name of inputs.packageNames) { packages.add(name); references.add(graph.packages.get(name).directory); }
      inputs.externalDependencies.forEach(name => packages.add(name));
      inputs.manifestPaths.forEach(path => references.add(path));
      projects++;
    }
    function visit(name, hooks = !ignoreScripts) {
      if (pending.has(name)) fail("workspace-check-script-cycle");
      const command = manifest.scripts[name];
      if (typeof command !== "string" || !command.trim()) fail("workspace-check-script-missing");
      pending.add(name);
      if (hooks && Object.hasOwn(manifest.scripts, `pre${name}`)) visit(`pre${name}`, false);
      for (const segment of command.split(" && ")) {
        // This is a deliberately closed command shape, not a shell parser.
        // Quotes, interpolation, redirects and alternate operators require an
        // explicit adapter rather than silently losing dependency observations.
        if (!/^[A-Za-z0-9_@./: -]+$/.test(segment) || segment.includes("  ")) fail("workspace-check-command-unsupported");
        const args = segment.split(" ");
        if (args[0] === "npm" && args[1] === "run" && args.length === 3 && scriptName(args[2])) visit(args[2]);
        else if (args[0] === "node" && args[1] === "scripts/repo/workspace-build/script.mjs") {
          const options = workspaceCompilerOptions(args.slice(2), graph.root);
          project(options.project, options.selection);
        } else if (["tsc", "node_modules/.bin/tsc"].includes(args[0]) && ["-p", "--project"].includes(args[1]) && args.length === 3) {
          const owner = selectWorkspaceProject(graph, args[2]);
          project(args[2], { roots: [owner], includeRootDevDependencies: true });
        } else if (args[0] === "node" && args.length === 2 && /\.[cm]?js$/.test(args[1])) {
          checkedPath(args[1]); references.add(args[1]);
        } else fail("workspace-check-command-unsupported");
      }
      if (hooks && Object.hasOwn(manifest.scripts, `post${name}`)) visit(`post${name}`, false);
      pending.delete(name);
    }
    visit(selected.npmScript, !ignoreScripts);
    if (!projects) fail("workspace-check-project-missing");
    contexts[checkContextKey(selected)] = { references: [...references].sort(), nodePackages: [...packages].sort(), ignoreScripts };
  }
  return { contexts, discoveryInputs };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.length !== 2) fail("workspace-check-arguments-invalid");
    const input = readFileSync(0, "utf8");
    if (input.length > 1024 * 1024) fail("workspace-check-selection-invalid");
    const request = JSON.parse(input);
    process.stdout.write(JSON.stringify(workspaceCheckInputs(process.cwd(), request.scripts)) + "\n");
  } catch (error) {
    const known = error instanceof WorkspaceCheckInputError || error instanceof WorkspaceDeclarationError || error instanceof WorkspaceCompilationError;
    process.stdout.write(JSON.stringify({ error: known ? error.code : "workspace-check-observation-unavailable" }) + "\n");
    process.exitCode = 1;
  }
}
