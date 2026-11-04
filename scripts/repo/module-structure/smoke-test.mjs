// agentic-artifact:
//   schema: agentic-artifact/v3
//   id: repo.module-structure.tests
//   version: 5
//   status: active
//   created_on: "2026-11-01"
//   updated_on: "2026-11-02"
//   layer: 03.product
//   domain: architecture
//   disciplines: [architecture, agentic]
//   kind: script
//   purpose: Prove export-only indexes, bounded legacy debt and safe findings.
//   portability: {class: source-only, targets: []}
//   effects: [read-only]
//   used_by:
//   - id: repo.module-structure.regression
//     path: scripts/repo/module-structure/smoke-test.sh
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { checkIndexes, discoverIndexes, discoverModuleSources, workspaceAliases, governedIndex, inspectIndex, inspectModuleDependencies, inspectConfigurationAccess, safeReport } from "./check.mjs";

const config = "packages/core/src/config/index.ts";
const legacy = "platform/example/src/index.ts";
const empty = { schema: "repo/module-index-legacy/v1", legacy: [] };
const exported = 'export { read } from "./readers";\nexport type { Source } from "./types";\nexport * from "./issues";\n';
const sources = text => new Map([[config, text]]);
const codes = report => report.findings.map(item => item.code);
const ordinaryConfigurationCaller = 'apps/future/src/features/connect.ts';
const access = (text, name = ordinaryConfigurationCaller) => inspectConfigurationAccess(new Map([[name, text]]));
for (const text of [
  'connect(process.env.PORT);', 'const source = process["env"];',
  'const { env: values } = process;', 'connect(globalThis.process.env.PORT);',
  'connect(globalThis["process"]["env"].PORT);',
  'import nodeProcess from "node:process"; connect(nodeProcess.env.PORT);',
  'import * as nodeProcess from "process"; connect(nodeProcess["env"].PORT);',
  'import { default as nodeProcess } from "node:process"; connect(nodeProcess.env.PORT);',
  'import { env as values } from "node:process"; connect(values.PORT);',
  'const nodeProcess = require("node:process"); connect(nodeProcess.env.PORT);',
  'const {env: values} = require("process"); connect(values.PORT);',
  'connect((process as NodeJS.Process).env.PORT);',
]) {
  assert.ok(codes(access(text)).includes('CONFIGURATION_SOURCE_ACCESS_OUTSIDE_LOADER'), text);
}
for (const text of [
  'import { validateConfigSettings } from "@kanbien/core/config"; const result = validateConfigSettings(source, definitions);',
  'import { checkedConfiguration } from "@fixture/config"; const result = checkedConfiguration(source);',
  'export function connectChecked(configuration) { return connect(configuration.port); }',
  'import { validateCertificateAuthorityContent } from "@kanbien/platform-security"; validateCertificateAuthorityContent(text);',
  'export function local(process) { return process.env; }',
  'const process = {env: {mode: "fixture"}}; use(process.env);',
  'type Environment = typeof process.env;',
  '// process.env.PRIVATE\nconst example = "process.env.PRIVATE";',
]) assert.deepEqual(access(text).findings, [], text);
for (const name of ['platform/config/src/load.ts', 'platform/server/src/main.ts', 'platform/workers/src/main.ts',
  'infra/04.deploy/03.product/entrypoints/future.main.ts', 'apps/future/tests/fixture.ts', 'apps/future/src/connect.test.ts']) {
  assert.deepEqual(access('const source = process.env;', name).findings, [], name);
}
for (const name of ['packages/core/src/config/domain/reading/source.ts', 'platform/future/src/handler.ts', 'products/future/src/features/task.ts']) {
  assert.ok(codes(access('const source = process.env;', name)).includes('CONFIGURATION_SOURCE_ACCESS_OUTSIDE_LOADER'), name);
}
assert.deepEqual(codes(access('const invalid = {')), ['CONFIGURATION_ACCESS_SYNTAX_INVALID']);
assert.equal(JSON.stringify(safeReport(access('use(process.env.SYNTHETIC_PRIVATE_CANARY);'))).includes('SYNTHETIC_PRIVATE_CANARY'), false);
assert.deepEqual(codes(checkIndexes(sources(exported), empty)), []);
assert.deepEqual(codes(checkIndexes(sources('// function fake() {}\nexport {};\n;'), empty)), []);
const forbidden = [
  'export function read() { return 1; }', 'const value = 1;', 'export const value = 1;',
  'export type Value = string;', 'export interface Source {}', 'export class Reader {}',
  'export enum Choice { One }', 'export namespace Values {}', 'import type { Source } from "./types";',
  'import "./startup";', 'start();', 'export default start();', 'export import helper = require("helper");',
];
for (const text of forbidden) {
  const result = checkIndexes(sources(exported + text), empty);
  assert.ok(codes(result).includes("MODULE_INDEX_IMPLEMENTATION"), text);
  assert.equal(result.findings[0].line, 4);
}
assert.deepEqual(codes(checkIndexes(sources('export function {'), empty)), ['MODULE_INDEX_SYNTAX_INVALID']);

const original = 'export function old() { return 1; }';
const allowance = { schema: empty.schema, legacy: [{ path: legacy,
  sha256: inspectIndex(legacy, original).fingerprint, reason: 'Existing implementation; explicit reviewed debt.' }] };
const fixture = new Map([[config, exported], [legacy, original]]);
assert.equal(checkIndexes(fixture, allowance).legacy, 1);
assert.deepEqual(codes(checkIndexes(fixture, allowance)), []);
fixture.set(legacy, original + '\nexport { next } from "./next";');
assert.deepEqual(codes(checkIndexes(fixture, allowance)), []);
for (const text of [original + '\nconst newlyAdded = 1;', original.replace('return 1', 'return 2')]) {
  fixture.set(legacy, text);
  assert.deepEqual(codes(checkIndexes(fixture, allowance)), ['MODULE_INDEX_LEGACY_CHANGED']);
}
fixture.set(legacy, exported);
assert.deepEqual(codes(checkIndexes(fixture, allowance)), ['MODULE_INDEX_LEGACY_STALE']);
assert.deepEqual(codes(checkIndexes(fixture, empty)), []);
fixture.delete(legacy);
assert.deepEqual(codes(checkIndexes(fixture, allowance)), ['MODULE_INDEX_LEGACY_STALE']);
fixture.set('apps/future/src/index.ts', 'export const newValue = 1;');
assert.deepEqual(codes(checkIndexes(fixture, empty)), ['MODULE_INDEX_IMPLEMENTATION']);
fixture.delete('apps/future/src/index.ts');
fixture.set('platform/future/src/values.ts', 'export const value = 1;');
assert.deepEqual(codes(checkIndexes(fixture, empty)), []);
fixture.delete(config);
assert.ok(codes(checkIndexes(fixture, empty)).includes('MODULE_INDEX_REQUIRED_MISSING'));
for (const bad of [null, {}, { schema: empty.schema, legacy: [{}] },
  { schema: empty.schema, legacy: [allowance.legacy[0], allowance.legacy[0]] },
  { schema: empty.schema, legacy: [{ ...allowance.legacy[0], path: config }] },
  { schema: empty.schema, legacy: [{ ...allowance.legacy[0], path: '../escape/src/index.ts' }] }]) {
  assert.deepEqual(codes(checkIndexes(sources(exported), bad)), ['MODULE_INDEX_BASELINE_INVALID']);
}
assert.equal(governedIndex('packages/future/src/submodule/index.ts'), true);
assert.equal(governedIndex('products/future/src/index.tsx'), true);
assert.equal(governedIndex('platform/example/tests/fixtures/src/index.ts'), false);
assert.equal(governedIndex('infra/entrypoints/index.ts'), false);
const canary = 'sensitive-canary';
assert.equal(JSON.stringify(safeReport(inspectIndex(config, `export const password = "${canary}";`))).includes(canary), false);
assert.equal(safeReport({ findings: [{ code: 'MODULE_INDEX_IMPLEMENTATION', path: 'apps/\nunsafe/src/index.ts', line: 1 }] }).findings[0].path, 'unavailable');

const root = new URL('../../../', import.meta.url);
const directory = name => ({ name, isDirectory: () => true, isSymbolicLink: () => false });
const file = name => ({ name, isDirectory: () => false, isSymbolicLink: () => false });
const virtualRoot = '/fixture';
const virtual = {
  async readdir(name) {
    if (name === '/fixture/apps') return [directory('new-app')];
    if (name === '/fixture/apps/new-app') return [directory('src'), directory('tests')];
    if (name === '/fixture/apps/new-app/src') return [file('index.ts'), file('values.ts')];
    if (name.endsWith('/tests')) throw new Error('Excluded fixture must not be traversed');
    return [];
  },
  async readFile(name) { assert.equal(name, '/fixture/apps/new-app/src/index.ts'); return exported; },
};
assert.deepEqual([...await discoverIndexes(virtualRoot, virtual)], [['apps/new-app/src/index.ts', exported]]);
await assert.rejects(discoverIndexes(virtualRoot, { ...virtual, readFile: async () => { throw new Error(canary); } }));
await assert.rejects(discoverIndexes(virtualRoot, { ...virtual, readdir: async () => [{ name: 'linked-source', isSymbolicLink: () => true }] }), /MODULE_INDEX_SOURCE_UNREADABLE/);
const cli = spawnSync('bash', ['scripts/repo/module-structure/script.sh', canary], {
  cwd: fileURLToPath(root), encoding: 'utf8',
});
assert.equal(cli.status, 2);
assert.deepEqual(JSON.parse(cli.stdout).findings, [{ code: 'MODULE_INDEX_ARGUMENTS_INVALID' }]);
assert.equal((cli.stdout + cli.stderr).includes(canary), false);
const baseline = JSON.parse(await readFile(new URL('legacy.v1.json', import.meta.url), 'utf8'));
const actual = await discoverIndexes(fileURLToPath(root));
const actualConfigurationSources = await discoverModuleSources(fileURLToPath(root));
assert.deepEqual(inspectConfigurationAccess(actualConfigurationSources).findings, []);
const futureConfigurationSources = new Map(actualConfigurationSources);
futureConfigurationSources.set('apps/future/src/features/unchecked.ts', 'connect(process.env.PORT);');
assert.ok(codes(inspectConfigurationAccess(futureConfigurationSources)).includes('CONFIGURATION_SOURCE_ACCESS_OUTSIDE_LOADER'));
const current = checkIndexes(actual, baseline);
assert.deepEqual(current.findings, []);
assert.deepEqual(inspectIndex(config, actual.get(config)).findings, []);
const mutant = new Map(actual);
mutant.set(config, actual.get(config) + '\nexport function forbiddenRegression() { return 1; }\n');
assert.ok(codes(checkIndexes(mutant, baseline)).includes('MODULE_INDEX_IMPLEMENTATION'));
console.log(`Module structure fixtures passed; actual ${current.indexes} indexes, ${current.legacy} pinned legacy indexes; config regression rejected.`);

const moduleRoot = 'packages/future/src/example';
const publicIndex = `${moduleRoot}/index.ts`;
const contract = `${moduleRoot}/contract/types.ts`;
const capability = `${moduleRoot}/domain/read.ts`;
const caller = 'platform/consumer/src/call.ts';
const graph = new Map([
  [publicIndex, 'export { read } from "./domain/read";'],
  [contract, 'export type Value = string;'],
  [capability, 'import type { Value } from "../contract/types"; export function read(): Value { return "accepted"; }'],
  [caller, 'import { read } from "@fixture/example";'],
]);
const aliases = new Map([['@fixture/example', publicIndex]]);
assert.deepEqual(inspectModuleDependencies(graph, aliases), { findings: [], modules: 1 });
const tsxGraph = new Map(graph);
tsxGraph.delete(publicIndex);
tsxGraph.set(`${moduleRoot}/index.tsx`, 'export { read } from "./domain/read.js";');
tsxGraph.set(caller, 'import { read } from "../../../packages/future/src/example/index.js";');
assert.deepEqual(inspectModuleDependencies(tsxGraph).findings, []);
function rejects(name, text, expected) {
  const changed = new Map(graph); changed.set(name, text);
  assert.ok(codes(inspectModuleDependencies(changed, aliases)).includes(expected), expected);
}
rejects(contract, 'import { read } from "../domain/read";', 'MODULE_CONTRACT_CAPABILITY_IMPORT');
rejects(contract, 'export type Rejected = import("../domain/read").Value;', 'MODULE_CONTRACT_CAPABILITY_IMPORT');
rejects(capability, 'import { read } from "../index";', 'MODULE_OWN_INDEX_IMPORT');
rejects(capability, 'export { read } from "../index.js";', 'MODULE_DEPENDENCY_CYCLE');
rejects(caller, 'import { read } from "../../../packages/future/src/example/domain/read";', 'MODULE_PRIVATE_IMPORT');
rejects(caller, 'const read = require("@fixture/example/domain/read");', 'MODULE_PRIVATE_IMPORT');
rejects(caller, 'const result = import("@fixture/example/contract/types");', 'MODULE_PRIVATE_IMPORT');
rejects(capability, 'const dependency = import(selectedName);', 'MODULE_DEPENDENCY_DYNAMIC_UNRESOLVED');
rejects(contract, 'import type { Missing } from "./absent";', 'MODULE_DEPENDENCY_UNRESOLVED');
rejects(contract, 'export type {', 'MODULE_DEPENDENCY_SYNTAX_INVALID');
const indirect = new Map(graph);
indirect.set(contract, 'export { read } from "../bridge";');
indirect.set(`${moduleRoot}/bridge.ts`, 'export { read } from "./domain/read";');
assert.ok(codes(inspectModuleDependencies(indirect, aliases)).includes('MODULE_CONTRACT_CAPABILITY_IMPORT'));
const typeCycle = new Map(graph);
typeCycle.set(contract, 'import type { Failure } from "./errors";');
typeCycle.set(`${moduleRoot}/contract/errors.ts`, 'import type { Value } from "./types";');
assert.ok(codes(inspectModuleDependencies(typeCycle, aliases)).includes('MODULE_DEPENDENCY_CYCLE'));
const assembled = new Map([
  ['packages/core/src/config/index.ts', 'export * from "./contract/reporting/diagnostics";'],
  ['packages/core/src/config/contract/reporting/diagnostics.ts', 'export const definitions = [];'],
  ['packages/core/src/diagnostic-catalog.ts', 'import { definitions } from "./config/contract/reporting/diagnostics";'],
]);
assert.deepEqual(inspectModuleDependencies(assembled).findings, []);
assembled.set('packages/core/src/diagnostic-catalog.ts', 'import { errors } from "./config/contract/reporting/errors";');
assembled.set('packages/core/src/config/contract/reporting/errors.ts', 'export const errors = [];');
assert.ok(codes(inspectModuleDependencies(assembled)).includes('MODULE_PRIVATE_IMPORT'));

// Nested responsibility groups retain the same boundaries, including type edges.
const nestedContract = `${moduleRoot}/contract/reporting/issues.ts`;
const nestedRead = `${moduleRoot}/domain/reading/source.ts`;
const nestedCheck = `${moduleRoot}/domain/validation/settings.ts`;
const nested = new Map([
  [publicIndex, 'export { read } from "./domain/reading/source";'],
  [nestedContract, 'export type Value = string;'],
  [nestedRead, 'import type { Value } from "../../contract/reporting/issues"; export function read(): Value { return "accepted"; }'],
  [nestedCheck, 'import { read } from "../reading/source"; export const check = read;'],
  [caller, 'import { read } from "@fixture/example";'],
]);
assert.deepEqual(inspectModuleDependencies(nested, aliases).findings, []);
for (const [file, text, code] of [
  [nestedContract, 'import type { Value } from "../../domain/reading/source";', 'MODULE_CONTRACT_CAPABILITY_IMPORT'],
  [nestedRead, 'import type { Value } from "../../index";', 'MODULE_OWN_INDEX_IMPORT'],
  [caller, 'import type { Value } from "@fixture/example/contract/reporting/issues";', 'MODULE_PRIVATE_IMPORT'],
  [nestedRead, 'import type { Value } from "../validation/settings";', 'MODULE_DEPENDENCY_CYCLE'],
]) {
  const rejected = new Map(nested); rejected.set(file, text);
  assert.ok(codes(inspectModuleDependencies(rejected, aliases)).includes(code), code);
}
for (const privateTarget of ['errors', 'setting-issues', 'diagnostics']) {
  const rejected = new Map(assembled);
  rejected.set('packages/core/src/diagnostic-catalog.ts', 'import { definitions } from "./config/contract/reporting/diagnostics";');
  const target = `packages/core/src/config/contract/reporting/${privateTarget}.ts`;
  rejected.set(target, 'export const value = 1;');
  rejected.set('platform/consumer/src/call.ts', `import { value } from "../../../${target.slice(0, -3)}";`);
  assert.ok(inspectModuleDependencies(rejected).findings.some(finding =>
    finding.code === 'MODULE_PRIVATE_IMPORT' && finding.path === 'platform/consumer/src/call.ts'));
}
const actualSources = await discoverModuleSources(fileURLToPath(root));
const actualDependencies = inspectModuleDependencies(actualSources, await workspaceAliases(fileURLToPath(root)));
assert.deepEqual(actualDependencies.findings, []);
assert.ok(actualDependencies.modules >= 1);
console.log(`Module dependency fixtures passed; ${actualDependencies.modules} adopted module(s), including type cycles, private aliases, dynamic imports and the exact catalog exception.`);

// The cleaned reference indexes must not drift back behind legacy allowances.
const currentAllowances = JSON.parse(await readFile(new URL("./legacy.v1.json", import.meta.url), "utf8"));
for (const file of ["platform/config/src/index.ts", "platform/adapters/aws/persistence/postgresql/src/index.ts",
  "platform/adapters/aws/persistence/postgresql/src/configuration/index.ts"]) {
  const text = await readFile(new URL("../../../" + file, import.meta.url), "utf8");
  assert.deepEqual(inspectIndex(file, text).findings, [], file);
  assert.equal(currentAllowances.legacy.some(item => item.path === file), false, "do not re-pin a cleaned index");
}
