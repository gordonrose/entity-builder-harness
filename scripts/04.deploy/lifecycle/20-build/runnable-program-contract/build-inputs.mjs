// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: deploy.runnable-program.build-inputs
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 04.deploy
//   domain: deployment.package-candidates
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Bind existing runnable-program dependency approvals to declaration-derived compiler and package inputs.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: infra.04-deploy.03-product.entrypoints.runnable-program-index
//     path: infra/04.deploy/03.product/entrypoints/runnable-program-index.yml

import { readFileSync, realpathSync, statSync } from "node:fs";
import { builtinModules } from "node:module";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseDocument } from "yaml";
import { deriveWorkspaceInputs, loadWorkspaceGraph, WorkspaceDeclarationError } from "../../../../repo/workspace-build/declarations.mjs";

export class ProgramBuildInputError extends Error {
  constructor(code) { super(code); this.name = "ProgramBuildInputError"; this.code = code; }
}
const fail = code => { throw new ProgramBuildInputError(code); };
const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const id = value => typeof value === "string" && /^[a-z0-9][a-z0-9-]*$/.test(value);
const name = value => typeof value === "string" && /^(?:@[a-z0-9][a-z0-9._-]*\/)?[a-z0-9][a-z0-9._-]*$/.test(value);
const path = value => typeof value === "string" && value.length > 0
  && value.split("/").every(part => /^[A-Za-z0-9_.-]+$/.test(part) && part !== "." && part !== "..");
const list = (value, check) => Array.isArray(value) && value.every(check) && new Set(value).size === value.length;

function source(root, relative) {
  if (!path(relative)) fail("program-build-path-invalid");
  const absolute = join(root, relative);
  let properties;
  try {
    if (realpathSync(absolute) !== absolute) fail("program-build-source-symlink");
    properties = statSync(absolute);
  } catch (error) {
    if (error instanceof ProgramBuildInputError) throw error;
    fail("program-build-source-unreadable");
  }
  if (!properties.isFile() || properties.size > 1024 * 1024) fail("program-build-source-invalid");
  return absolute;
}

export function readProgramBuildInputs(repository, options = {}) {
  if (!object(options) || !id(options.programId)) fail("program-build-selection-invalid");
  const graph = loadWorkspaceGraph(repository);
  const contractPath = options.contractPath ?? "infra/04.deploy/03.product/entrypoints/runnable-program-index.yml";
  const absolute = source(graph.root, contractPath);
  let text;
  try { text = readFileSync(absolute, "utf8"); }
  catch { fail("program-build-source-unreadable"); }
  let declaration;
  try {
    const document = parseDocument(text, { strict: true, uniqueKeys: true, prettyErrors: false, version: "1.2", schema: "core" });
    if (document.errors.length || document.warnings.length) fail("program-build-declaration-invalid");
    declaration = document.toJS({ maxAliasCount: 0 });
  } catch { fail("program-build-declaration-invalid"); }
  if (!object(declaration) || declaration.schema !== "deploy/runnable-program-contract/v1"
    || !object(declaration.dependency_bindings) || !Array.isArray(declaration.runnable_programs)) fail("program-build-declaration-invalid");
  const ids = declaration.runnable_programs.map(program => object(program) ? program.id : undefined);
  if (!list(ids, id)) fail("program-build-records-invalid");
  const program = declaration.runnable_programs.find(program => program.id === options.programId);
  if (!program) fail("program-build-record-missing");
  if (!object(program.build) || program.build.kind !== "workspace-typescript"
    || !path(program.build.typescript_project) || !program.build.typescript_project.endsWith(".json")) fail("program-build-project-invalid");
  source(graph.root, program.build.typescript_project);
  if (!list(program.approved_dependencies, id) || !program.approved_dependencies.length
    || !list(program.forbidden_dependencies, id) || !list(program.observed_dependencies, id)) fail("program-build-dependencies-invalid");
  if (program.approved_dependencies.some(dependency => program.forbidden_dependencies.includes(dependency))
    || program.observed_dependencies.some(dependency => !program.approved_dependencies.includes(dependency))) fail("program-build-dependency-not-approved");
  const roots = [], external = new Set(), workspaceOwners = {}, externalOwners = {};
  for (const dependency of program.approved_dependencies) {
    const binding = declaration.dependency_bindings[dependency];
    if (!object(binding) || Object.keys(binding).length !== 1) fail("program-build-binding-invalid");
    if (Object.hasOwn(binding, "workspace_package")) {
      if (!name(binding.workspace_package) || roots.includes(binding.workspace_package)) fail("program-build-binding-invalid");
      roots.push(binding.workspace_package);
      workspaceOwners[binding.workspace_package] = dependency;
    } else if (Object.hasOwn(binding, "external_packages")) {
      if (!list(binding.external_packages, name) || !binding.external_packages.length) fail("program-build-binding-invalid");
      for (const packageName of binding.external_packages) {
        if (graph.packages.has(packageName) || external.has(packageName)) fail("program-build-binding-invalid");
        external.add(packageName);
        externalOwners[packageName] = dependency;
      }
    } else fail("program-build-binding-invalid");
  }
  const selection = { roots: roots.sort(), allowedPackages: [...roots].sort() };
  const inputs = deriveWorkspaceInputs(graph, selection);
  if (inputs.externalDependencies.some(dependency => !external.has(dependency))) fail("program-build-external-dependency-not-approved");
  return { programId: program.id, project: program.build.typescript_project, selection, inputs,
    approvedDependencies: [...program.approved_dependencies], observedDependencies: [...program.observed_dependencies],
    forbiddenDependencies: [...program.forbidden_dependencies], externalOwners,
    nodeBuiltins: [...builtinModules].sort(),
    workspaceOwners: Object.fromEntries(Object.entries(workspaceOwners).map(([name, owner]) => [graph.packages.get(name).directory + "/", owner])),
    manifestPaths: [...new Set([...inputs.manifestPaths, contractPath, program.build.typescript_project])].sort() };
}

// This is a read-only projection for existing Python contract/import observers.
// It neither invokes a compiler nor turns discovered dependencies into approval.
if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2), options = {};
    if (args.length !== 2 && args.length !== 4) fail("program-build-selection-invalid");
    for (let index = 0; index < args.length; index += 2) {
      const key = args[index] === "--program" ? "programId" : args[index] === "--contract" ? "contractPath" : undefined;
      if (!key || Object.hasOwn(options, key) || !args[index + 1]) fail("program-build-selection-invalid");
      options[key] = args[index + 1];
    }
    process.stdout.write(JSON.stringify(readProgramBuildInputs(process.cwd(), options)) + "\n");
  } catch (error) {
    const known = error instanceof ProgramBuildInputError || error instanceof WorkspaceDeclarationError;
    process.stdout.write(JSON.stringify({ error: known ? error.code : "program-build-observation-unavailable" }) + "\n");
    process.exitCode = 1;
  }
}
