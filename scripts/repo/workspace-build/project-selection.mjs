// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.project-selection
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.declarations
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Derive legacy build workspace roots from explicit TypeScript project roots without treating resolved imports as approval.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: repo.workspace-build.command
//     path: scripts/repo/workspace-build/script.mjs

import { realpathSync, statSync } from "node:fs";
import { isAbsolute, relative, resolve, sep } from "node:path";
import ts from "typescript";
import { deriveWorkspaceInputs, loadWorkspaceGraph, selectWorkspaceProject, WorkspaceDeclarationError } from "./declarations.mjs";

const fail = code => { throw new WorkspaceDeclarationError(code); };
const safePrefix = value => typeof value === "string" && value.endsWith("/")
  && value.slice(0, -1).split("/").every(part => /^[A-Za-z0-9_.-]+$/.test(part) && part !== "." && part !== "..");

export function projectWorkspaceInputs(repository, project, options = {}) {
  if (!options || typeof options !== "object" || Array.isArray(options)
    || Object.keys(options).some(key => !["unownedRootPrefixes", "allowMissingJsonAssets"].includes(key))) fail("workspace-project-invalid");
  const { unownedRootPrefixes = [], allowMissingJsonAssets = false } = options;
  const graph = loadWorkspaceGraph(repository);
  if (typeof project !== "string" || !project.endsWith(".json") || project.includes("\0")
    || !Array.isArray(unownedRootPrefixes) || !unownedRootPrefixes.every(safePrefix)
    || typeof allowMissingJsonAssets !== "boolean") fail("workspace-project-invalid");
  function checked(file) {
    const absolute = resolve(graph.root, file), distance = relative(graph.root, absolute);
    if (distance === ".." || distance.startsWith(`..${sep}`) || isAbsolute(distance)) fail("workspace-project-root-escaped");
    try {
      if (realpathSync(absolute) !== absolute) fail("workspace-source-symlink");
      if (!statSync(absolute).isFile()) fail("workspace-project-source-invalid");
    } catch (error) {
      if (error instanceof WorkspaceDeclarationError) throw error;
      fail("workspace-project-source-unavailable");
    }
    return { absolute, relative: distance.split(sep).join("/") };
  }
  const selected = checked(project), failures = [];
  let config;
  try {
    config = ts.getParsedCommandLineOfConfigFile(selected.absolute, {}, {
      ...ts.sys, onUnRecoverableConfigFileDiagnostic(value) { failures.push(value.code); },
    });
  } catch { fail("workspace-project-invalid"); }
  if (!config || config.errors.length || failures.length || config.projectReferences?.length) fail("workspace-project-invalid");
  const roots = new Set(), rootFiles = [], unownedRootFiles = [];
  for (const filename of config.fileNames) {
    const file = checked(filename); rootFiles.push(file.relative);
    try { roots.add(selectWorkspaceProject(graph, file.relative)); }
    catch (error) {
      if (!(error instanceof WorkspaceDeclarationError) || error.code !== "workspace-project-owner-missing") throw error;
      if (!unownedRootPrefixes.some(prefix => file.relative.startsWith(prefix))) fail("workspace-project-root-unowned");
      unownedRootFiles.push(file.relative);
    }
  }
  if (!roots.size) fail("workspace-project-workspaces-empty");
  const selection = { roots: [...roots].sort(), ...(allowMissingJsonAssets ? { allowMissingJsonAssets: true } : {}) };
  return { project: selected.relative, selection, inputs: deriveWorkspaceInputs(graph, selection),
    rootFiles: rootFiles.sort(), unownedRootFiles: unownedRootFiles.sort() };
}
