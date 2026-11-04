// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.module-structure.check
//   version: 4
//   status: active
//   created_on: "2026-11-01"
//   updated_on: "2026-11-02"
//   layer: 03.product
//   domain: architecture
//   disciplines: [architecture, agentic]
//   kind: script
//   purpose: Check public indexes, adopted module dependency boundaries and narrow configuration source access.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: repo.module-structure.command
//     path: scripts/repo/module-structure/script.sh
import { createHash } from "node:crypto";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

export const sourceRoots = Object.freeze(["packages", "platform", "apps", "products"]);
const excluded = new Set(["node_modules", ".git", "dist", "build", "tests", "fixtures", "__tests__"]);
const strictIndexes = new Set(["packages/core/src/config/index.ts"]);
const baselinePath = "scripts/repo/module-structure/legacy.v1.json";
const schema = "repo/module-index-legacy/v1";

export function governedIndex(name) {
  if (typeof name !== "string") return false;
  const parts = name.split("/");
  return sourceRoots.includes(parts[0]) && parts.includes("src")
    && /\/index\.tsx?$/.test(name) && !parts.some(part => excluded.has(part))
    && !parts.includes("..") && !name.includes("\\");
}

export function inspectIndex(name, text) {
  const source = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true);
  if (source.parseDiagnostics.length) return { findings: [{ code: "MODULE_INDEX_SYNTAX_INVALID", path: name, line: 1 }], fingerprint: null };
  const declarations = source.statements.filter(statement =>
    !ts.isExportDeclaration(statement) && !ts.isEmptyStatement(statement));
  return {
    fingerprint: createHash("sha256").update(JSON.stringify(declarations.map(node => node.getText(source)))).digest("hex"),
    findings: declarations.map(node => ({
      code: "MODULE_INDEX_IMPLEMENTATION", path: name,
      line: source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1,
    })),
  };
}

export function checkIndexes(sources, baseline) {
  const invalid = () => ({ findings: [{ code: "MODULE_INDEX_BASELINE_INVALID" }], indexes: sources.size, legacy: 0 });
  if (baseline?.schema !== schema || !Array.isArray(baseline.legacy)) return invalid();
  const allowances = new Map();
  for (const entry of baseline.legacy) {
    if (!entry || !governedIndex(entry.path) || strictIndexes.has(entry.path)
      || allowances.has(entry.path) || typeof entry.sha256 !== "string" || !/^[a-f0-9]{64}$/.test(entry.sha256)
      || typeof entry.reason !== "string" || !entry.reason.trim()) return invalid();
    allowances.set(entry.path, entry);
  }
  const findings = [];
  let legacy = 0;
  for (const [name, text] of [...sources].sort(([a], [b]) => a.localeCompare(b))) {
    if (!governedIndex(name)) continue;
    const result = inspectIndex(name, text);
    const allowance = allowances.get(name);
    if (result.fingerprint === null) findings.push(...result.findings);
    else if (allowance) {
      if (!result.findings.length) findings.push({ code: "MODULE_INDEX_LEGACY_STALE", path: name, line: 1 });
      else if (allowance.sha256 !== result.fingerprint) findings.push({ code: "MODULE_INDEX_LEGACY_CHANGED", path: name, line: 1 });
      else legacy++;
    } else findings.push(...result.findings);
  }
  for (const name of allowances.keys()) {
    if (!sources.has(name)) findings.push({ code: "MODULE_INDEX_LEGACY_STALE", path: name, line: 1 });
  }
  for (const name of strictIndexes) {
    if (!sources.has(name)) findings.push({ code: "MODULE_INDEX_REQUIRED_MISSING", path: name, line: 1 });
  }
  return { findings, indexes: [...sources.keys()].filter(governedIndex).length, legacy };
}

/** A narrow source-access boundary, not a proof that results are checked or used. */
export function inspectConfigurationAccess(sources) {
  const findings = [];
  const loaders = new Set(['platform/server/src/main.ts', 'platform/workers/src/main.ts']);
  const binds = (name, expected) => ts.isIdentifier(name) ? name.text === expected
    : (ts.isObjectBindingPattern(name) || ts.isArrayBindingPattern(name))
      && name.elements.some(item => ts.isBindingElement(item) && binds(item.name, expected));
  const member = node => ts.isPropertyAccessExpression(node) ? node.name.text
    : ts.isElementAccessExpression(node) && node.argumentExpression && ts.isStringLiteralLike(node.argumentExpression)
      ? node.argumentExpression.text : undefined;
  const processImport = node => ts.isStringLiteralLike(node) && ['process', 'node:process'].includes(node.text);
  for (const [name, text] of sources) {
    if (!/^(?:packages|platform|apps|products)\/.*\/src\//.test(name)
      || !/\.tsx?$/.test(name) || /\.(?:test|spec)\.tsx?$/.test(name)
      || name.split('/').some(part => excluded.has(part))) continue;
    if (name.startsWith('platform/config/src/') || loaders.has(name)) continue;
    const source = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true);
    if (source.parseDiagnostics.length) {
      findings.push({ code: 'CONFIGURATION_ACCESS_SYNTAX_INVALID', path: name, line: 1 }); continue;
    }
    const issue = node => findings.push({ code: 'CONFIGURATION_SOURCE_ACCESS_OUTSIDE_LOADER', path: name,
      line: source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1 });
    // Resolve only direct lexical declarations; arbitrary alias/data flow stays a review duty.
    function binding(identifier) {
      for (let scope = identifier.parent; scope; scope = scope.parent) {
        if (ts.isFunctionLike(scope)) {
          const parameter = scope.parameters.find(item => binds(item.name, identifier.text));
          if (parameter) return parameter;
        }
        if (ts.isCatchClause(scope) && scope.variableDeclaration && binds(scope.variableDeclaration.name, identifier.text)) return scope.variableDeclaration;
        if (!ts.isSourceFile(scope) && !ts.isBlock(scope)) continue;
        for (const statement of scope.statements) {
          if (ts.isVariableStatement(statement)) {
            const declaration = statement.declarationList.declarations.find(item => binds(item.name, identifier.text));
            if (declaration) return declaration;
          }
          if (ts.isImportDeclaration(statement) && !statement.importClause?.isTypeOnly) {
            const clause = statement.importClause;
            if (clause?.name?.text === identifier.text) return statement;
            if (clause?.namedBindings && (ts.isNamespaceImport(clause.namedBindings)
              ? clause.namedBindings.name.text === identifier.text
              : clause.namedBindings.elements.some(item => !item.isTypeOnly && item.name.text === identifier.text))) return statement;
          }
          if ((ts.isFunctionDeclaration(statement) || ts.isClassDeclaration(statement)) && statement.name?.text === identifier.text) return statement;
        }
      }
      return undefined;
    }
    const processRequire = node => node && ts.isCallExpression(node) && ts.isIdentifier(node.expression)
      && node.expression.text === 'require' && !binding(node.expression) && node.arguments.length === 1 && processImport(node.arguments[0]);
    function processObject(node) {
      if (ts.isParenthesizedExpression(node) || ts.isAsExpression(node) || ts.isNonNullExpression(node)) return processObject(node.expression);
      if (ts.isIdentifier(node)) {
        const declaration = binding(node);
        if (!declaration) return node.text === 'process';
        if (ts.isImportDeclaration(declaration) && processImport(declaration.moduleSpecifier)) {
          const clause = declaration.importClause;
          return clause?.name?.text === node.text || (clause?.namedBindings && ts.isNamespaceImport(clause.namedBindings)
            && clause.namedBindings.name.text === node.text)
            || (clause?.namedBindings && ts.isNamedImports(clause.namedBindings)
              && clause.namedBindings.elements.some(item => item.name.text === node.text && (item.propertyName?.text ?? item.name.text) === 'default'));
        }
        return ts.isVariableDeclaration(declaration) && ts.isIdentifier(declaration.name) && processRequire(declaration.initializer);
      }
      return processRequire(node) || ((ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node))
        && member(node) === 'process' && ts.isIdentifier(node.expression) && node.expression.text === 'globalThis' && !binding(node.expression));
    }
    function visit(node) {
      if (ts.isTypeNode(node)) return;
      if (ts.isImportDeclaration(node) && processImport(node.moduleSpecifier) && !node.importClause?.isTypeOnly
        && node.importClause?.namedBindings && ts.isNamedImports(node.importClause.namedBindings)
        && node.importClause.namedBindings.elements.some(item => !item.isTypeOnly && (item.propertyName?.text ?? item.name.text) === 'env')) issue(node);
      if ((ts.isPropertyAccessExpression(node) || ts.isElementAccessExpression(node)) && member(node) === 'env' && processObject(node.expression)) issue(node);
      if (ts.isVariableDeclaration(node) && node.initializer && ts.isObjectBindingPattern(node.name)
        && processObject(node.initializer) && node.name.elements.some(item => (item.propertyName?.getText(source) ?? item.name.getText(source)).replace(/^['"]|['"]$/g, '') === 'env')) issue(node);
      ts.forEachChild(node, visit);
    }
    visit(source);
  }
  return { findings };
}

/** Modules opt in through their actual role folders and public index, not a manifest. */
export function inspectModuleDependencies(sources, aliases = new Map()) {
  const modules = new Set();
  for (const name of sources.keys()) {
    const match = name.match(/^(.*\/src(?:\/[^/]+)*)\/(?:contract|domain)\/[^]*\.tsx?$/);
    if (match && (sources.has(`${match[1]}/index.ts`) || sources.has(`${match[1]}/index.tsx`))) modules.add(match[1]);
  }
  const owner = name => [...modules].filter(root => name.startsWith(`${root}/`)).sort((a, b) => b.length - a.length)[0];
  const publicIndex = (name, root) => name === `${root}/index.ts` || name === `${root}/index.tsx`;
  const candidates = base => [base, `${base}.ts`, `${base}.tsx`, `${base}/index.ts`, `${base}/index.tsx`];
  const resolve = (from, specifier) => {
    let base;
    if (specifier.startsWith('.')) base = path.posix.normalize(path.posix.join(path.posix.dirname(from), specifier));
    else {
      const alias = [...aliases.keys()].filter(key => specifier === key || specifier.startsWith(`${key}/`)).sort((a, b) => b.length - a.length)[0];
      if (alias) {
        const suffix = specifier.slice(alias.length);
        base = suffix ? `${aliases.get(alias).replace(/\/index\.tsx?$/, '')}${suffix}` : aliases.get(alias);
      }
    }
    if (base === undefined) return undefined;
    if (/\.[cm]?jsx?$/.test(base)) base = base.replace(/\.[cm]?jsx?$/, '');
    return candidates(base).find(name => sources.has(name));
  };
  const findings = [], edges = new Map();
  const issue = (code, name, node, source) => findings.push({ code, path: name, line: source.getLineAndCharacterOfPosition(node.getStart(source)).line + 1 });
  for (const [name, text] of sources) {
    const source = ts.createSourceFile(name, text, ts.ScriptTarget.Latest, true);
    const own = owner(name);
    if (own && source.parseDiagnostics.length) { findings.push({ code: 'MODULE_DEPENDENCY_SYNTAX_INVALID', path: name, line: 1 }); continue; }
    const dependencies = [];
    function visit(node) {
      let expression;
      if (ts.isImportDeclaration(node) || ts.isExportDeclaration(node)) expression = node.moduleSpecifier;
      else if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) expression = node.moduleReference.expression;
      else if (ts.isImportTypeNode(node) && ts.isLiteralTypeNode(node.argument)) expression = node.argument.literal;
      else if (ts.isCallExpression(node) && (node.expression.kind === ts.SyntaxKind.ImportKeyword || (ts.isIdentifier(node.expression) && node.expression.text === 'require'))) expression = node.arguments[0];
      if (expression) {
        if (ts.isStringLiteralLike(expression)) dependencies.push({ specifier: expression.text, node });
        else if (own) issue('MODULE_DEPENDENCY_DYNAMIC_UNRESOLVED', name, node, source);
      }
      ts.forEachChild(node, visit);
    }
    visit(source);
    const links = [];
    for (const { specifier, node } of dependencies) {
      const target = resolve(name, specifier), targetOwner = target && owner(target);
      if (!target) {
        if (own && specifier.startsWith('.')) issue('MODULE_DEPENDENCY_UNRESOLVED', name, node, source);
        continue;
      }
      links.push({ target, node, source });
      if (own && !publicIndex(name, own) && publicIndex(target, own)) issue('MODULE_OWN_INDEX_IMPORT', name, node, source);
      const catalogAssembly = name === 'packages/core/src/diagnostic-catalog.ts'
        && target === 'packages/core/src/config/contract/reporting/diagnostics.ts';
      if (targetOwner && own !== targetOwner && !publicIndex(target, targetOwner) && !catalogAssembly) issue('MODULE_PRIVATE_IMPORT', name, node, source);
    }
    edges.set(name, links);
  }
  function reaches(start, predicate, scope, seen = new Set()) {
    if (seen.has(start)) return false;
    seen.add(start);
    return (edges.get(start) ?? []).some(({ target }) => owner(target) === scope && (predicate(target) || reaches(target, predicate, scope, seen)));
  }
  for (const [name, links] of edges) {
    const own = owner(name);
    if (!own) continue;
    for (const link of links) {
      if (owner(link.target) !== own) continue;
      if (name.startsWith(`${own}/contract/`) && (link.target.startsWith(`${own}/domain/`) || reaches(link.target, target => target.startsWith(`${own}/domain/`), own))) issue('MODULE_CONTRACT_CAPABILITY_IMPORT', name, link.node, link.source);
      if (link.target === name || reaches(link.target, target => target === name, own)) issue('MODULE_DEPENDENCY_CYCLE', name, link.node, link.source);
    }
  }
  return { findings, modules: modules.size };
}

async function discoverSources(root, io, indexesOnly) {
  const sources = new Map();
  async function walk(directory) {
    const entries = await io.readdir(path.join(root, directory), { withFileTypes: true });
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      if (excluded.has(entry.name)) continue;
      const name = `${directory}/${entry.name}`;
      if (entry.isSymbolicLink()) throw new Error("MODULE_INDEX_SOURCE_UNREADABLE");
      if (entry.isDirectory()) await walk(name);
      else if (indexesOnly ? governedIndex(name) : /\.tsx?$/.test(name)) sources.set(name, await io.readFile(path.join(root, name), "utf8"));
    }
  }
  for (const directory of indexesOnly ? sourceRoots : [...sourceRoots, 'infra']) await walk(directory);
  return sources;
}

export function discoverIndexes(root, io = { readdir, readFile }) { return discoverSources(root, io, true); }
export function discoverModuleSources(root, io = { readdir, readFile }) { return discoverSources(root, io, false); }

export async function workspaceAliases(root) {
  const aliases = new Map();
  async function walk(directory) {
    for (const entry of await readdir(path.join(root, directory), { withFileTypes: true })) {
      if (excluded.has(entry.name)) continue;
      const name = `${directory}/${entry.name}`;
      if (entry.isSymbolicLink()) throw new Error('MODULE_INDEX_SOURCE_UNREADABLE');
      if (entry.isDirectory()) await walk(name);
      else if (entry.name === 'package.json') {
        const manifest = JSON.parse(await readFile(path.join(root, name), 'utf8'));
        if (typeof manifest.name !== 'string') continue;
        for (const [key, value] of Object.entries(manifest.exports ?? {})) {
          if (typeof value !== 'string' || !value.startsWith('./')) continue;
          aliases.set(manifest.name + (key === '.' ? '' : key.slice(1)), path.posix.normalize(path.posix.join(directory, entry.name, '..', value)));
        }
      }
    }
  }
  for (const directory of sourceRoots) await walk(directory);
  return aliases;
}

export function safeReport(report) {
  return { ...report, findings: report.findings.map(({ code, path: name, line }) => ({
    code,
    ...(name === undefined ? {} : { path: /^[A-Za-z0-9_./@+-]+$/.test(name) ? name : "unavailable" }),
    ...(line === undefined ? {} : { line }),
  })) };
}

async function main() {
  if (process.argv.length !== 2) {
    console.log(JSON.stringify({ findings: [{ code: "MODULE_INDEX_ARGUMENTS_INVALID" }] }));
    process.exitCode = 2;
    return;
  }
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
  let baseline;
  try { baseline = JSON.parse(await readFile(path.join(root, baselinePath), "utf8")); }
  catch { console.log(JSON.stringify({ findings: [{ code: "MODULE_INDEX_BASELINE_UNREADABLE" }] })); process.exitCode = 1; return; }
  let sources, aliases;
  try { sources = await discoverModuleSources(root); aliases = await workspaceAliases(root); }
  catch { console.log(JSON.stringify({ findings: [{ code: "MODULE_INDEX_SOURCE_UNREADABLE" }] })); process.exitCode = 1; return; }
  const indexes = checkIndexes(sources, baseline), dependencies = inspectModuleDependencies(sources, aliases);
  const access = inspectConfigurationAccess(sources);
  const report = safeReport({ ...indexes, modules: dependencies.modules, findings: [...indexes.findings, ...dependencies.findings, ...access.findings] });
  console.log(JSON.stringify(report));
  if (report.findings.length) process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(() => { console.log(JSON.stringify({ findings: [{ code: "MODULE_INDEX_CHECK_FAILED" }] })); process.exitCode = 1; });
}
