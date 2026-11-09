// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.script.entity-smoke.prepare-dependencies
//   version: 1
//   status: draft
//   created_on: "2026-11-08"
//   updated_on: "2026-11-09"
//   layer: 04.deploy
//   domain: deployment.entity-smoke
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Copy only the locked installed dependency closure for the selected feature image without flattening nested versions.
//   portability: {class: internal, targets: []}
//   effects: [writes-files]
//   used_by:
//   - id: infra.04-deploy.entity-smoke.image.dockerfile
//     path: infra/04.deploy/03.product/image/entity-smoke/Dockerfile

import { cpSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, realpathSync } from "node:fs";
import { basename, dirname, isAbsolute, join, relative, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const roots = ["pg", "@aws-sdk/rds-signer"];
const packageName = /^(?:@[a-z0-9_.-]+\/)?[a-z0-9_.-]+$/;
class PreparationFailure extends Error {
  constructor(phase, reason, effect = "not-started") { super("ENTITY_SMOKE_DEPENDENCIES_NOT_PREPARED"); this.phase = phase; this.reason = reason; this.effect = effect; }
}
function reject(phase, reason, effect) { throw new PreparationFailure(phase, reason, effect); }
function contained(root, path) { const value = relative(root, path); return value !== ".." && !value.startsWith("../") && !isAbsolute(value); }
function present(path) {
  try { lstatSync(path); return true; }
  catch (cause) { if (cause?.code === "ENOENT") return false; throw cause; }
}
function manifest(path) {
  try { const value = JSON.parse(readFileSync(path, "utf8")); if (!value || typeof value !== "object" || Array.isArray(value)) throw Error(); return value; }
  catch { reject("manifest", "unreadable-or-invalid"); }
}
function noLinks(root, path) {
  if (!contained(root, path)) reject("source", "outside-installed-tree");
  let current = path;
  while (current !== root) {
    if (lstatSync(current).isSymbolicLink()) reject("source", "symlink-not-permitted");
    current = dirname(current);
  }
}

/** The source is npm ci's installed tree, never a caller-provided package list.
 * Preserve npm's relative layout, including installed optional and peer edges. */
export function dependencyClosure(repository) {
  repository = realpathSync(repository);
  const installed = join(repository, "node_modules"), lock = manifest(join(repository, "package-lock.json"));
  if (lock.lockfileVersion !== 3 || !lock.packages || typeof lock.packages !== "object" || Array.isArray(lock.packages)) reject("manifest", "lock-unsupported");
  if (lstatSync(installed).isSymbolicLink()) reject("source", "symlink-not-permitted");
  const selected = new Map();
  function locate(name, parent, optional) {
    if (!packageName.test(name) || name.split("/").some(part => part === "." || part === "..")) reject("manifest", "dependency-name-invalid");
    let current = parent;
    while (contained(repository, current)) {
      const path = join(current, "node_modules", name);
      if (basename(current) !== "node_modules" && present(path)) { noLinks(repository, path); return path; }
      if (current === repository) break;
      current = dirname(current);
    }
    if (!optional) reject("resolution", "required-dependency-missing");
    return undefined;
  }
  function visit(name, parent, optional = false) {
    const path = locate(name, parent, optional);
    if (!path) return;
    const key = relative(repository, path).replaceAll("\\", "/");
    if (selected.has(key)) return;
    const pkg = manifest(join(path, "package.json")), locked = lock.packages[key];
    if (pkg.name !== name || typeof pkg.version !== "string" || !locked || locked.link === true || locked.version !== pkg.version) reject("manifest", "installed-lock-mismatch");
    selected.set(key, { path, name, version: pkg.version });
    const edges = new Map();
    for (const [field, defaultOptional] of [["dependencies", false], ["optionalDependencies", true], ["peerDependencies", false]]) {
      const values = pkg[field] ?? {};
      if (!values || typeof values !== "object" || Array.isArray(values)) reject("manifest", "dependency-map-invalid");
      for (const [dependency, range] of Object.entries(values)) {
        if (typeof range !== "string" || !range) reject("manifest", "dependency-map-invalid");
        // optionalDependencies overrides dependencies; a required peer cannot
        // erase a required ordinary edge, or vice versa.
        const isOptional = defaultOptional || field === "peerDependencies" && pkg.peerDependenciesMeta?.[dependency]?.optional === true;
        if (field === "optionalDependencies" || !edges.has(dependency)) edges.set(dependency, isOptional);
        else edges.set(dependency, edges.get(dependency) && isOptional);
      }
    }
    for (const [dependency, isOptional] of edges) visit(dependency, path, isOptional);
  }
  for (const name of roots) visit(name, repository);
  return [...selected.entries()].sort(([a], [b]) => a.localeCompare(b)).map(([location, pkg]) => ({ location, ...pkg }));
}

function verifyFiles(directory) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isSymbolicLink()) reject("source", "symlink-not-permitted");
    if (entry.name === "node_modules") continue; // separately resolved edges
    if (entry.isDirectory()) verifyFiles(path);
    else if (!entry.isFile()) reject("source", "non-regular-file");
  }
}
export function prepareDependencies(repository, destination, dryRun = false) {
  let writing = false;
  try {
    repository = realpathSync(repository); destination = resolve(destination);
    // A new directory only. Never merge into or overwrite an installed tree.
    if (present(destination) || contained(repository, destination) || contained(destination, repository)) reject("destination", "existing-or-overlapping");
    let ancestor = dirname(destination);
    while (!existsSync(ancestor)) ancestor = dirname(ancestor);
    if (realpathSync(ancestor) !== ancestor) reject("destination", "symlink-not-permitted");
    const closure = dependencyClosure(repository);
    for (const pkg of closure) verifyFiles(pkg.path);
    if (!dryRun) {
      writing = true; mkdirSync(destination, { recursive: true });
      for (const pkg of closure) {
        const output = join(destination, pkg.location.slice("node_modules/".length));
        mkdirSync(dirname(output), { recursive: true });
        cpSync(pkg.path, output, { recursive: true, errorOnExist: true, force: false,
          filter: source => source === pkg.path || !relative(pkg.path, source).split(/[\\/]/).includes("node_modules") });
      }
    }
    return { schema: "deploy/entity-smoke-dependencies/v1", verdict: dryRun ? "planned" : "prepared", roots, packages: closure.map(({ location, name, version }) => ({ location, name, version })) };
  } catch (cause) {
    if (cause instanceof PreparationFailure) { if (writing) cause.effect = "earlier-writes-possible"; throw cause; }
    reject(writing ? "copy" : "source", "unavailable", writing ? "earlier-writes-possible" : "not-started");
  }
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const args = process.argv.slice(2);
    if (args.length < 2 || args.length > 3 || args[2] !== undefined && args[2] !== "--dry-run") reject("arguments", "invalid");
    console.log(JSON.stringify(prepareDependencies(args[0], args[1], args[2] === "--dry-run")));
  } catch (cause) {
    console.error(JSON.stringify({ verdict: "failed", code: "ENTITY_SMOKE_DEPENDENCIES_NOT_PREPARED",
      phase: cause instanceof PreparationFailure ? cause.phase : "arguments", reason: cause instanceof PreparationFailure ? cause.reason : "invalid",
      effect: cause instanceof PreparationFailure ? cause.effect : "not-started" }));
    process.exitCode = 1;
  }
}
