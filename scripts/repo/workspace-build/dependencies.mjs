// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.dependencies
//   version: 1
//   status: draft
//   created_on: "2026-11-15"
//   updated_on: "2026-11-15"
//   layer: 06.shared
//   domain: build.declarations
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Inspect literal workspace imports against declared runtime and test dependency ownership.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: repo.module-structure.check
//     path: scripts/repo/module-structure/check.mjs

import { lstatSync, readFileSync, readdirSync } from "node:fs";
import { builtinModules } from "node:module";
import { isAbsolute, join, relative, resolve, sep } from "node:path";
import ts from "typescript";
import { deriveWorkspaceInputs, loadWorkspaceGraph, selectWorkspaceProject, WorkspaceDeclarationError } from "./declarations.mjs";

const excluded = new Set(["node_modules", ".git", ".cache", "dist", "build", "coverage"]);
const builtins = new Set(builtinModules.flatMap(name => [name, `node:${name}`]));
const sourceFile = name => /\.(?:[cm]?[jt]sx?)$/.test(name) && !/\.d\.[cm]?ts$/.test(name);
const developmentFile = name => ["tests", "__tests__", "fixtures"].includes(name.split("/")[0]) || /\.(?:test|spec)\.[cm]?[jt]sx?$/.test(name);
const packageName = specifier => specifier.startsWith("@") ? specifier.split("/").slice(0, 2).join("/") : specifier.split("/")[0];
const inside = (root, file) => { const distance = relative(root, file); return distance !== ".." && !distance.startsWith(`..${sep}`) && !isAbsolute(distance); };

/** Static literal imports only; computed loading is counted, not approved. */
export function inspectWorkspaceDependencies(root) {
  const graph = loadWorkspaceGraph(root), findings = [], seenFindings = new Set();
  const all = deriveWorkspaceInputs(graph, { roots: [...graph.packages.keys()] });
  const options = { module: ts.ModuleKind.NodeNext, moduleResolution: ts.ModuleResolutionKind.NodeNext,
    target: ts.ScriptTarget.ES2022, allowJs: true, resolveJsonModule: true,
    baseUrl: graph.root, paths: all.compilerPaths };
  const cache = ts.createModuleResolutionCache(graph.root, value => value, options);
  const parsed = new Map(), closures = new Map(), visited = new Set();
  let files = 0, imports = 0, computedImports = 0;
  const add = (code, path, line = 1) => {
    const key = `${code}:${path}:${line}`;
    if (!seenFindings.has(key)) { seenFindings.add(key); findings.push({ code, path, line }); }
  };
  const owner = file => {
    try { return selectWorkspaceProject(graph, file); }
    catch (error) { if (error instanceof WorkspaceDeclarationError && error.code === "workspace-project-owner-missing") return undefined; throw error; }
  };
  const isDevelopment = file => {
    const name = owner(file);
    return Boolean(name && developmentFile(relative(graph.packages.get(name).directory, file).split(sep).join("/")));
  };
  const declared = (manifest, development) => new Set(Object.keys({ ...manifest.dependencies, ...(development ? manifest.devDependencies : {}) }));
  const rootManifest = JSON.parse(readFileSync(join(graph.root, "package.json"), "utf8"));
  function closure(name) {
    if (!closures.has(name)) closures.set(name, deriveWorkspaceInputs(graph, { roots: [name], includeRootDevDependencies: true }));
    return closures.get(name);
  }
  function literals(file) {
    if (parsed.has(file)) return parsed.get(file);
    let component = graph.root;
    for (const part of file.split("/")) {
      component = join(component, part);
      if (lstatSync(component).isSymbolicLink()) {
        add("WORKSPACE_SOURCE_SYMLINK", file); parsed.set(file, []); return [];
      }
    }
    const text = readFileSync(join(graph.root, file), "utf8");
    const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true), result = [];
    files++;
    if (source.parseDiagnostics.length) add("WORKSPACE_SOURCE_SYNTAX_INVALID", file);
    const requires = new Set(["require"]);
    function discover(node) {
      if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.initializer
        && ts.isCallExpression(node.initializer) && ts.isIdentifier(node.initializer.expression)
        && node.initializer.expression.text === "createRequire") requires.add(node.name.text);
      ts.forEachChild(node, discover);
    }
    discover(source);
    function visit(node) {
      let value;
      if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) value = node.moduleSpecifier;
      else if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) value = node.moduleReference.expression;
      else if (ts.isImportTypeNode(node) && ts.isLiteralTypeNode(node.argument)) value = node.argument.literal;
      else if (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword
        || (ts.isIdentifier(node.expression) && requires.has(node.expression.text)))) {
        value = node.arguments[0];
        if (!value || !ts.isStringLiteralLike(value)) computedImports++;
      }
      if (value && ts.isStringLiteralLike(value)) result.push({ specifier: value.text, line: source.getLineAndCharacterOfPosition(value.getStart(source)).line + 1 });
      ts.forEachChild(node, visit);
    }
    visit(source); parsed.set(file, result); return result;
  }
  function inspect(file, context) {
    const visitKey = `${file}:${context.kind}:${context.owner ?? "root"}`;
    if (visited.has(visitKey)) return;
    visited.add(visitKey);
    const currentOwner = owner(file), development = isDevelopment(file);
    const manifest = currentOwner ? graph.packages.get(currentOwner).manifest : rootManifest;
    const allowed = context.kind === "entrypoint"
      ? new Set([...closure(context.owner).packageNames, ...closure(context.owner).externalDependencies])
      : declared(manifest, context.kind === "tooling" || development);
    for (const { specifier, line } of literals(file)) {
      imports++;
      if (builtins.has(specifier)) continue;
      const bare = !specifier.startsWith(".") && !isAbsolute(specifier);
      const dependency = bare ? packageName(specifier) : undefined;
      if (bare && dependency !== currentOwner && !allowed.has(dependency)) add("WORKSPACE_DEPENDENCY_UNDECLARED", file, line);
      if (bare && graph.packages.has(dependency) && !Object.hasOwn(all.compilerPaths, specifier)) add("WORKSPACE_EXPORT_UNDECLARED", file, line);
      const resolved = ts.resolveModuleName(specifier, join(graph.root, file), options, ts.sys, cache).resolvedModule?.resolvedFileName;
      if (!resolved) {
        if (!bare || graph.packages.has(dependency) || graph.workspaceLinks.has(dependency)) add("WORKSPACE_IMPORT_UNRESOLVED", file, line);
        continue;
      }
      if (!inside(graph.root, resolved)) { if (!bare) add("WORKSPACE_IMPORT_ESCAPES_REPOSITORY", file, line); continue; }
      const target = relative(graph.root, resolved).split(sep).join("/");
      if (target.split("/").includes("node_modules")) continue;
      const targetOwner = owner(target);
      if (targetOwner) {
        if (targetOwner !== currentOwner && !allowed.has(targetOwner)) add("WORKSPACE_DEPENDENCY_UNDECLARED", file, line);
        if ((context.kind === "entrypoint" || (context.kind === "workspace" && !development)) && isDevelopment(target)) {
          add("WORKSPACE_RUNTIME_TEST_DEPENDENCY", file, line);
        }
        // Every workspace source is inspected under its own manifest, not a
        // caller's broader development closure.
        continue;
      }
      if (!sourceFile(target)) continue;
      if (context.kind === "tooling" || ((development || context.kind === "entrypoint") && target.startsWith("scripts/"))) {
        inspect(target, { kind: "tooling" });
      } else if (context.kind === "entrypoint" || (development && target.startsWith("infra/"))) {
        inspect(target, { kind: "entrypoint", owner: context.owner ?? currentOwner });
      } else add("WORKSPACE_SOURCE_OWNER_MISSING", file, line);
    }
  }
  function walk(directory, expectedOwner) {
    for (const entry of readdirSync(join(graph.root, directory), { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      if (excluded.has(entry.name)) continue;
      const file = `${directory}/${entry.name}`;
      if (entry.isSymbolicLink()) { add("WORKSPACE_SOURCE_SYMLINK", file); continue; }
      if (entry.isDirectory()) { if (owner(file) === expectedOwner) walk(file, expectedOwner); }
      else if (sourceFile(file)) inspect(file, { kind: "workspace", owner: expectedOwner });
    }
  }
  for (const [name, record] of graph.packages) walk(record.directory, name);
  return { files, imports, computedImports, findings: findings.sort((a, b) => a.path.localeCompare(b.path) || a.line - b.line || a.code.localeCompare(b.code)) };
}
