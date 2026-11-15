// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.declarations
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.declarations
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Derive selected compiler and runtime inputs from existing workspace package declarations without writing files.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: deploy.plan.consolidate-core-platform-deployment-routes
//     path: .agentic/04.deploy/plans/implementation/consolidate-core-platform-deployment-routes.md

import { lstatSync, readFileSync, readdirSync, realpathSync } from "node:fs";
import { isAbsolute, join, relative, resolve, sep } from "node:path";

// Only code-owned observations cross this boundary, never rejected values or
// native filesystem messages. Callers own their operation/effect envelopes.
export class WorkspaceDeclarationError extends Error {
  constructor(code) { super(code); this.name = "WorkspaceDeclarationError"; this.code = code; }
}
const fail = code => { throw new WorkspaceDeclarationError(code); };
const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const packageName = value => typeof value === "string" && /^(?:@[a-z0-9][a-z0-9._-]*\/)?[a-z0-9][a-z0-9._-]*$/.test(value);
const safePath = value => typeof value === "string" && value.length > 0
  && value.split("/").every(part => /^[A-Za-z0-9_@.-]+$/.test(part) && part !== "." && part !== "..");

function stat(root, path) {
  let current = root;
  for (const part of path.split("/")) {
    current = join(current, part);
    let entry;
    try { entry = lstatSync(current); }
    catch (error) { if (error.code === "ENOENT") return undefined; fail("workspace-source-unreadable"); }
    if (entry.isSymbolicLink()) fail("workspace-source-symlink");
  }
  try { return lstatSync(current); }
  catch { fail("workspace-source-unreadable"); }
}

function readObject(root, path) {
  if (!stat(root, path)?.isFile()) fail("workspace-manifest-missing");
  let text;
  try { text = readFileSync(join(root, path), "utf8"); }
  catch { fail("workspace-manifest-unreadable"); }
  let value;
  try { value = JSON.parse(text); }
  catch { fail("workspace-manifest-invalid-json"); }
  if (!object(value)) fail("workspace-manifest-invalid");
  return value;
}

export function loadWorkspaceGraph(repository) {
  if (typeof repository !== "string" || !repository.length) fail("workspace-root-invalid");
  const root = resolve(repository);
  let canonical;
  try { canonical = realpathSync(root); }
  catch { fail("workspace-root-unreadable"); }
  if (canonical !== root) fail("workspace-source-symlink");
  const manifest = readObject(root, "package.json");
  if (!Array.isArray(manifest.workspaces) || !manifest.workspaces.length) fail("workspace-patterns-missing");
  const directories = new Set();
  for (const pattern of manifest.workspaces) {
    if (typeof pattern !== "string" || !pattern.split("/").every(part => part === "*" || safePath(part))) fail("workspace-pattern-unsupported");
    let candidates = [""];
    for (const part of pattern.split("/")) {
      const next = [];
      for (const parent of candidates) {
        if (part !== "*") {
          const path = parent ? `${parent}/${part}` : part;
          if (stat(root, path)?.isDirectory()) next.push(path);
          continue;
        }
        let entries;
        try { entries = readdirSync(join(root, parent), { withFileTypes: true }); }
        catch { fail("workspace-directory-unreadable"); }
        for (const entry of entries) {
          if (entry.isSymbolicLink()) fail("workspace-source-symlink");
          if (entry.isDirectory()) {
            if (!safePath(entry.name)) fail("workspace-path-unsupported");
            next.push(parent ? `${parent}/${entry.name}` : entry.name);
          }
        }
      }
      candidates = next;
    }
    candidates.forEach(path => directories.add(path));
  }
  const packages = new Map();
  for (const directory of [...directories].sort()) {
    const manifestPath = `${directory}/package.json`;
    if (!stat(root, manifestPath)) continue;
    const value = readObject(root, manifestPath);
    if (!packageName(value.name)) fail("workspace-package-name-invalid");
    if (packages.has(value.name)) fail("workspace-package-name-duplicate");
    packages.set(value.name, { directory, manifestPath, manifest: value });
  }
  const workspaceLinks = new Set(), lockPath = "package-lock.json";
  const hasLock = Boolean(stat(root, lockPath));
  if (hasLock) {
    const lock = readObject(root, lockPath);
    if (!object(lock.packages)) fail("workspace-lock-invalid");
    for (const [path, entry] of Object.entries(lock.packages)) {
      if (object(entry) && entry.link === true && path.startsWith("node_modules/")) workspaceLinks.add(path.slice(13));
    }
  }
  return { root, packages, workspaceLinks, manifestPaths: ["package.json", ...(hasLock ? [lockPath] : [])] };
}

export function selectWorkspaceProject(graph, project) {
  if (!object(graph) || typeof graph.root !== "string" || !(graph.packages instanceof Map)) fail("workspace-graph-invalid");
  if (typeof project !== "string" || !project || project.includes("\0")) fail("workspace-project-invalid");
  const target = resolve(graph.root, project);
  const owners = [...graph.packages.entries()].filter(([, record]) => {
    const distance = relative(resolve(graph.root, record.directory), target);
    return distance !== ".." && !distance.startsWith(`..${sep}`) && !isAbsolute(distance);
  }).sort((left, right) => right[1].directory.length - left[1].directory.length);
  if (!owners.length) fail("workspace-project-owner-missing");
  return owners[0][0];
}

export function deriveWorkspaceInputs(graph, selection = {}) {
  if (!object(graph) || typeof graph.root !== "string" || !(graph.packages instanceof Map)
    || !(graph.workspaceLinks instanceof Set) || !Array.isArray(graph.manifestPaths)) fail("workspace-graph-invalid");
  if (!object(selection)) fail("workspace-selection-invalid");
  const { roots, includeRootDevDependencies = false, allowedPackages, allowMissingJsonAssets = false } = selection;
  if (!Array.isArray(roots) || !roots.length || roots.some(name => !packageName(name))
    || new Set(roots).size !== roots.length || typeof includeRootDevDependencies !== "boolean"
    || typeof allowMissingJsonAssets !== "boolean") fail("workspace-selection-invalid");
  if (allowedPackages !== undefined && (!Array.isArray(allowedPackages)
    || allowedPackages.some(name => !packageName(name)) || new Set(allowedPackages).size !== allowedPackages.length)) fail("workspace-approval-invalid");
  const allowed = allowedPackages === undefined ? undefined : new Set(allowedPackages);
  const rootNames = new Set(roots), selected = new Map(), external = new Set(), pending = [...roots];
  while (pending.length) {
    const name = pending.shift();
    if (selected.has(name)) continue;
    if (allowed && !allowed.has(name)) fail("workspace-dependency-not-approved");
    const record = graph.packages.get(name);
    if (!record) fail("workspace-dependency-unresolved");
    const manifest = record.manifest;
    selected.set(name, record);
    // Workspace optional/peer selection needs deliberate semantics; external
    // installed-package optional/peer closure remains with the lock resolver.
    for (const field of ["optionalDependencies", "peerDependencies"]) {
      if (manifest[field] !== undefined && (!object(manifest[field]) || Object.keys(manifest[field]).length)) fail("workspace-dependency-kind-unsupported");
    }
    const fields = ["dependencies", ...(includeRootDevDependencies && rootNames.has(name) ? ["devDependencies"] : [])];
    for (const field of fields) {
      const dependencies = manifest[field] === undefined ? {} : manifest[field];
      if (!object(dependencies)) fail("workspace-dependencies-invalid");
      for (const [dependency, version] of Object.entries(dependencies)) {
        if (!packageName(dependency) || typeof version !== "string" || !version.length) fail("workspace-dependencies-invalid");
        if (graph.packages.has(dependency)) pending.push(dependency);
        else if (graph.workspaceLinks.has(dependency) || version.startsWith("workspace:")) fail("workspace-dependency-unresolved");
        else external.add(dependency);
      }
    }
  }
  const packages = {}, compilerPaths = {}, sourceFiles = new Set(), manifestPaths = new Set(graph.manifestPaths);
  for (const [name, record] of [...selected].sort(([a], [b]) => a.localeCompare(b))) {
    const exports = record.manifest.exports;
    if (!object(exports) || !Object.keys(exports).length) fail("workspace-exports-missing");
    const compiled = {};
    for (const [key, target] of Object.entries(exports).sort(([a], [b]) => a.localeCompare(b))) {
      if (key !== "." && (!key.startsWith("./") || !safePath(key.slice(2)))) fail("workspace-export-key-unsupported");
      if (typeof target !== "string" || !target.startsWith("./") || !safePath(target.slice(2))
        || !/\.(?:ts|json)$/.test(target) || target.endsWith(".d.ts")) fail("workspace-export-target-unsupported");
      const source = `${record.directory}/${target.slice(2)}`;
      try {
        const entry = stat(graph.root, source);
        // Catalogue generation owns declared JSON outputs. Only that explicit
        // path may defer their existence; present files and all TS sources keep
        // normal validation, and runtime assembly still validates before copying.
        if (!entry && allowMissingJsonAssets && source.endsWith(".json")) { /* Generated later by caller. */ }
        else if (!entry?.isFile()) fail("workspace-export-source-missing");
      } catch (error) {
        if (error instanceof WorkspaceDeclarationError) error.location = Object.freeze({ package: name, export: key });
        throw error;
      }
      compilerPaths[name + (key === "." ? "" : key.slice(1))] = [source];
      compiled[key] = source.replace(/\.ts$/, ".js");
      if (source.endsWith(".ts")) sourceFiles.add(source);
    }
    packages[name] = compiled;
    manifestPaths.add(record.manifestPath);
  }
  return { packages, compilerPaths, sourceFiles: [...sourceFiles].sort(), externalDependencies: [...external].sort(),
    manifestPaths: [...manifestPaths].sort(), packageNames: Object.keys(packages) };
}
