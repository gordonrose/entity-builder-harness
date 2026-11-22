// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.workspace-build.runtime-test-selection
//   version: 1
//   status: active
//   created_on: "2026-11-22"
//   updated_on: "2026-11-22"
//   layer: 06.shared
//   domain: testing.selection
//   disciplines: [architecture, security]
//   kind: script
//   purpose: Select source-affected TypeScript runtime tests from static relative imports, falling back to the full suite when that relationship is not provable.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: core.runtime-test-runner
//     path: packages/core/tests/run-runtime-tests.mjs

import { readdirSync, readFileSync, realpathSync, statSync } from "node:fs";
import { isAbsolute, relative, resolve, sep } from "node:path";
import ts from "typescript";

export class RuntimeTestSelectionError extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

const fail = code => { throw new RuntimeTestSelectionError(code); };
const relativeTypeScript = value => typeof value === "string" && value.startsWith(".");
const isTypeScript = value => value.endsWith(".ts") || value.endsWith(".tsx");
const safePath = value => typeof value === "string" && value.length > 0 && !value.includes("\\")
  && !value.includes("\0") && !isAbsolute(value) && value.split("/").every(part => part && part !== "." && part !== "..");

function repositoryPath(root, file) {
  const value = relative(root, file);
  if (!value || value === ".." || value.startsWith(`..${sep}`) || isAbsolute(value)) fail("runtime-test-selection-path-escaped");
  return value.split(sep).join("/");
}

function listedTypeScript(root, directory) {
  if (!safePath(directory)) fail("runtime-test-selection-directory-invalid");
  const absolute = resolve(root, directory);
  if (realpathSync(absolute) !== absolute || !statSync(absolute).isDirectory()) fail("runtime-test-selection-directory-invalid");
  const files = [];
  function visit(folder) {
    for (const entry of readdirSync(folder, { withFileTypes: true })) {
      const file = resolve(folder, entry.name);
      if (entry.isSymbolicLink()) fail("runtime-test-selection-symlink");
      if (entry.isDirectory()) visit(file);
      else if (entry.isFile() && isTypeScript(entry.name)) files.push(file);
    }
  }
  visit(absolute);
  return files.sort();
}

function resolveImport(root, known, sourceFile, specifier) {
  if (!relativeTypeScript(specifier)) return { dependency: undefined, unsafe: false };
  const target = resolve(sourceFile, "..", specifier);
  const stem = target.replace(/\.(?:[cm]?js|tsx?)$/, "");
  const candidates = [target, `${stem}.ts`, `${stem}.tsx`, resolve(stem, "index.ts"), resolve(stem, "index.tsx")];
  for (const candidate of candidates) {
    const path = repositoryPath(root, candidate);
    if (known.has(path)) return { dependency: path, unsafe: false };
  }
  return { dependency: undefined, unsafe: true };
}

function importsFor(root, known, path) {
  const source = ts.createSourceFile(path, readFileSync(resolve(root, path), "utf8"), ts.ScriptTarget.Latest, true);
  let unsafe = source.parseDiagnostics.length > 0;
  const dependencies = new Set();
  const consider = value => {
    if (typeof value !== "string") { unsafe = true; return; }
    const resolved = resolveImport(root, known, resolve(root, path), value);
    unsafe ||= resolved.unsafe;
    if (resolved.dependency) dependencies.add(resolved.dependency);
  };
  const visit = node => {
    if ((ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) && node.moduleSpecifier) {
      consider(ts.isStringLiteral(node.moduleSpecifier) ? node.moduleSpecifier.text : undefined);
    } else if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) {
      const expression = node.moduleReference.expression;
      consider(expression && ts.isStringLiteral(expression) ? expression.text : undefined);
    } else if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword) {
      // Import() is asynchronous runtime selection even when the current
      // specifier happens to be a literal. Do not infer a partial test set.
      unsafe = true;
    } else if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === "require") {
      const argument = node.arguments[0];
      consider(argument && ts.isStringLiteral(argument) ? argument.text : undefined);
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  return { dependencies, unsafe };
}

export function selectAffectedRuntimeTests({ root, sourceDirectory, testDirectory, changedPaths }) {
  const repository = resolve(root);
  if (realpathSync(repository) !== repository || !Array.isArray(changedPaths)
    || changedPaths.length === 0 || !changedPaths.every(safePath)) fail("runtime-test-selection-changed-path-invalid");
  const sourceFiles = listedTypeScript(repository, sourceDirectory);
  const testSources = listedTypeScript(repository, testDirectory);
  const testFiles = testSources.filter(path => path.endsWith("-runtime.test.ts"));
  if (!testFiles.length) fail("runtime-test-selection-tests-missing");
  // Helpers and type-level fixtures can sit between a runtime test and the
  // implementation. They belong to the graph even though only runtime files
  // can be executed by this selector.
  const known = new Set([...sourceFiles, ...testSources].map(file => repositoryPath(repository, file)));
  const runtimeTests = new Set(testFiles.map(file => repositoryPath(repository, file)));
  const reverse = new Map([...known].map(path => [path, new Set()]));
  let unsafe = false;
  for (const path of known) {
    const imports = importsFor(repository, known, path);
    unsafe ||= imports.unsafe;
    for (const dependency of imports.dependencies) reverse.get(dependency).add(path);
  }
  if (unsafe) return { mode: "full", reasons: ["dependency-analysis-unsafe"], testFiles: [...runtimeTests].sort() };
  if (changedPaths.some(path => !known.has(path))) return { mode: "full", reasons: ["changed-source-unowned"], testFiles: [...runtimeTests].sort() };
  const affected = new Set(changedPaths);
  const pending = [...changedPaths];
  while (pending.length) {
    const path = pending.pop();
    for (const importer of reverse.get(path)) {
      if (!affected.has(importer)) { affected.add(importer); pending.push(importer); }
    }
  }
  const selected = [...affected].filter(path => runtimeTests.has(path)).sort();
  return selected.length
    ? { mode: "affected", reasons: ["static-relative-imports"], testFiles: selected }
    : { mode: "full", reasons: ["affected-tests-unresolved"], testFiles: [...runtimeTests].sort() };
}
