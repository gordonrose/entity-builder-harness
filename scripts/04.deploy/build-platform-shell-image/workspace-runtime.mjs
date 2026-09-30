// agentic-artifact:
//   schema: agentic-artifact/v2
//   id: deploy.script.workspace-runtime-projection
//   version: 1
//   status: active
//   layer: 04.deploy
//   domain: deployment.realization
//   disciplines: [architecture, security, sre]
//   kind: script
//   purpose: Materialize only normalized compiler-bound workspace exports and reject stale targets or hidden generated files.
//   portability: {class: reusable, targets: [entity-builder]}
//   effects: [writes-files]
//   used_by:
//   - id: deploy.script.operational-realization-local-runtime
//     path: scripts/04.deploy/operational-realization-gate/local_runtime.py

import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import * as fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

let preparedInput = null;

const MAX_BYTES = 16 * 1024 * 1024;
const configurations = new Map([
  ['platform/server/tsconfig.image.json', '.cache/platform-shell-image-build'],
  ['platform/server/tsconfig.runtime-test.json', '.cache/platform-server-runtime'],
  ['products/kanbien-platform/tsconfig.runtime-test.json', '.cache/product-kanbien-platform-runtime'],
]);
const fail = () => { throw new Error('workspace-export-preparation-failed'); };
const hash = (raw) => 'sha256:' + createHash('sha256').update(raw).digest('hex');
const keys = (object, expected) => object && typeof object === 'object' && !Array.isArray(object)
  && JSON.stringify(Object.keys(object).sort()) === JSON.stringify([...expected].sort());
const canonical = (value) => {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(
    key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
  return JSON.stringify(value);
};
const safe = (value) => typeof value === 'string' && value.length <= 512 && /^[A-Za-z0-9_./@+-]+$/.test(value)
  && value.split('/').every(part => part && part !== '.' && part !== '..'
    && !['.git', '.aws', '.ssh', '.codex', '.agents', '.env', 'secret', 'secrets', 'credentials'].includes(part.toLowerCase()));
const digest = (value) => typeof value === 'string' && /^sha256:[0-9a-f]{64}$/.test(value);

function withParent(relative, createParents, action) {
  if (!safe(relative)) fail();
  const components = relative.split('/');
  let descriptor = fs.openSync('.', fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  try {
    for (const component of components.slice(0, -1)) {
      const anchored = `/proc/self/fd/${descriptor}/${component}`;
      let child;
      try { child = fs.openSync(anchored, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW); }
      catch (error) {
        if (error.code !== 'ENOENT' || !createParents) throw error;
        fs.mkdirSync(anchored, {mode: 0o700});
        child = fs.openSync(anchored, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
      }
      fs.closeSync(descriptor); descriptor = child;
    }
    return action(`/proc/self/fd/${descriptor}/${components.at(-1)}`);
  } finally { fs.closeSync(descriptor); }
}
function readDescriptor(descriptor) {
  const before = fs.fstatSync(descriptor);
  if (!before.isFile() || before.size > MAX_BYTES) fail();
  const buffer = Buffer.alloc(Math.min(MAX_BYTES + 1, before.size + 1));
  let total = 0;
  while (total < buffer.length) {
    const size = fs.readSync(descriptor, buffer, total, buffer.length - total, null);
    if (!size) break;
    total += size;
  }
  const after = fs.fstatSync(descriptor);
  if (before.size !== after.size || before.mtimeMs !== after.mtimeMs || before.ctimeMs !== after.ctimeMs
      || before.ino !== after.ino || total !== before.size) fail();
  return buffer.subarray(0, total);
}
function read(relative) {
  return withParent(relative, false, anchored => {
    const descriptor = fs.openSync(anchored, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
    try { return readDescriptor(descriptor); } finally { fs.closeSync(descriptor); }
  });
}
function write(relative, raw) {
  return withParent(relative, true, anchored => {
    let descriptor;
    try { descriptor = fs.openSync(anchored, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK); }
    catch (error) {
      if (error.code !== 'ENOENT') throw error;
      fs.writeFileSync(anchored, raw, {flag:'wx', mode:0o600});
      return;
    }
    try {
      if (!readDescriptor(descriptor).equals(raw)) fail();
    } finally { fs.closeSync(descriptor); }
  });
}
function tree(relative) {
  const result = new Map();
  let total = 0;
  let entries = 0;
  const root = fs.openSync('.', fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
  function visit(parent, name, prefix, depth) {
    if (depth > 40 || !safe(name)) fail();
    const descriptor = fs.openSync(`/proc/self/fd/${parent}/${name}`, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
    try {
      for (const child of fs.readdirSync(`/proc/self/fd/${descriptor}`).sort()) {
        if (++entries > 20000 || !safe(child) || child.includes('/')) fail();
        const anchored = `/proc/self/fd/${descriptor}/${child}`;
        const info = fs.lstatSync(anchored);
        if (info.isDirectory()) visit(descriptor, child, prefix + child + '/', depth + 1);
        else {
          if (!info.isFile() || info.size > MAX_BYTES || result.size >= 10000) fail();
          const fd = fs.openSync(anchored, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW | fs.constants.O_NONBLOCK);
          let raw; try { raw = readDescriptor(fd); } finally { fs.closeSync(fd); }
          total += raw.length; if (total > 32 * 1024 * 1024) fail();
          result.set(prefix + child, raw);
        }
      }
    } finally { fs.closeSync(descriptor); }
  }
  try {
    let descriptor = root;
    const held = [];
    try {
      const parts = relative.split('/');
      for (const part of parts.slice(0, -1)) {
        if (!safe(part)) fail();
        descriptor = fs.openSync(`/proc/self/fd/${descriptor}/${part}`, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY | fs.constants.O_NOFOLLOW);
        held.push(descriptor);
      }
      visit(descriptor, parts.at(-1), '', 0);
    } finally { for (const fd of held.reverse()) fs.closeSync(fd); }
  } finally { fs.closeSync(root); }
  return result;
}

function prepare(configuration, outputRoot) {
  if (configurations.get(configuration) !== outputRoot) fail();
  let raw;
  const arguments_ = process.argv.slice(2);
  if (arguments_.length !== 0) fail();
  if (preparedInput !== null) {
    if (preparedInput.configuration !== configuration) fail();
    raw = preparedInput.raw;
    preparedInput = null;
  } else {
    const child = spawnSync('python3', [
      'scripts/04.deploy/operational-realization-gate/package_exports_cli.py',
      '--prepare-existing', '--source-root', process.cwd(), '--configuration', configuration,
    ], { cwd: process.cwd(), env: { PATH: process.env.PATH ?? '/usr/bin:/bin', LANG: 'C.UTF-8', TZ: 'UTC' },
      maxBuffer: MAX_BYTES, timeout: 180000 });
    if (child.error || child.status !== 0 || child.stderr.length) fail();
    raw = child.stdout;
  }
  if (raw.length > MAX_BYTES) fail();
  const projection = JSON.parse(raw.toString('utf8'));
  const fields = ['schema', 'scope', 'authorized', 'configuration', 'output_root', 'source_inventory_digest',
    'export_inventory_digest', 'compiler_observation_digest', 'policy_revision', 'compiler_files', 'entries', 'projection_digest'];
  if (!keys(projection, fields) || projection.schema !== 'local-workspace-export-projection/v1'
      || projection.scope !== 'compiler-bound-runtime-exports' || projection.authorized !== false
      || projection.configuration !== configuration || projection.output_root !== outputRoot
      || !['source_inventory_digest','export_inventory_digest','compiler_observation_digest','policy_revision','projection_digest']
        .every(field => digest(projection[field])) || !Array.isArray(projection.entries)
      || projection.entries.length === 0 || projection.entries.length > 10000) fail();
  if (raw.toString('utf8').trim() !== canonical(projection)) fail();
  const body = { ...projection }; delete body.projection_digest;
  if (hash(Buffer.from(canonical(body))) !== projection.projection_digest) fail();
  if (!Array.isArray(projection.compiler_files) || !projection.compiler_files.length || projection.compiler_files.length > 10000) fail();
  const compilerFiles = new Map();
  for (const file of projection.compiler_files) {
    if (!keys(file, ['path','digest','bytes']) || !safe(file.path) || file.path.startsWith('node_modules/')
        || /\.(?:ts|tsx|mts|cts)$/.test(file.path) || !digest(file.digest)
        || !Number.isSafeInteger(file.bytes) || file.bytes < 0 || file.bytes > MAX_BYTES || compilerFiles.has(file.path)) fail();
    const content = read(outputRoot + '/' + file.path);
    if (hash(content) !== file.digest || content.length !== file.bytes) fail();
    compilerFiles.set(file.path, content);
  }
  const packages = new Map();
  const generated = new Map();
  const observedTargets = new Map();
  const seen = new Set();
  for (const entry of projection.entries) {
    if (!keys(entry, ['kind','declaration_id','package_name','subpath','source_path','source_digest','output_path','output_digest','output_bytes'])
        || !['package-export','executable-alias'].includes(entry.kind)
        || typeof entry.package_name !== 'string' || !/^(?:@[a-z0-9][a-z0-9._-]*\/)?[a-z0-9][a-z0-9._-]*$/.test(entry.package_name)
        || typeof entry.subpath !== 'string' || !/^\.(?:\/[A-Za-z0-9_-]+(?:\/[A-Za-z0-9_-]+)*)?$/.test(entry.subpath)
        || entry.subpath.split('/').some(part => part.toLowerCase() === 'node_modules')
        || !safe(entry.source_path) || !safe(entry.output_path) || entry.output_path.startsWith('node_modules/')
        || !/\.(?:js|cjs)$/.test(entry.output_path)
        || !['declaration_id','source_digest','output_digest'].every(field => digest(entry[field]))
        || !Number.isSafeInteger(entry.output_bytes) || entry.output_bytes < 0 || entry.output_bytes > MAX_BYTES) fail();
    const identity = entry.package_name + ':' + entry.subpath;
    if (seen.has(identity)) fail(); seen.add(identity);
    const targetPath = outputRoot + '/' + entry.output_path;
    const target = compilerFiles.get(entry.output_path);
    if (!target) fail();
    if (hash(target) !== entry.output_digest || target.length !== entry.output_bytes) fail();
    observedTargets.set(targetPath, target);
    const packageRoot = 'node_modules/' + entry.package_name;
    const shim = packageRoot + (entry.subpath === '.' ? '/index.js' : '/' + entry.subpath.slice(2) + '/index.js');
    let relative = path.posix.relative(path.posix.dirname(shim), entry.output_path);
    if (!relative.startsWith('.')) relative = './' + relative;
    generated.set(shim, Buffer.from('module.exports = require(' + JSON.stringify(relative) + ');\n'));
    if (!packages.has(entry.package_name)) packages.set(entry.package_name, {});
    packages.get(entry.package_name)[entry.subpath] = entry.subpath === '.' ? './index.js' : './' + entry.subpath.slice(2) + '/index.js';
  }
  for (const [name, exports] of packages) {
    const sortedExports = Object.fromEntries(Object.keys(exports).sort().map(key => [key, exports[key]]));
    generated.set('node_modules/' + name + '/package.json', Buffer.from(JSON.stringify({name, type:'commonjs', exports:sortedExports}, null, 2) + '\n'));
  }
  for (const relative of generated.keys()) {
    const parts = relative.split('/');
    for (let size = 1; size < parts.length; size++) if (generated.has(parts.slice(0, size).join('/'))) fail();
  }
  const expected = new Map([...compilerFiles, ...generated]);
  if (expected.size !== compilerFiles.size + generated.size) fail();
  const before = tree(outputRoot);
  for (const [relative, content] of before) if (!expected.get(relative)?.equals(content)) fail();
  if (before.size !== compilerFiles.size && before.size !== expected.size) fail();
  for (const [relative, content] of generated) write(outputRoot + '/' + relative, content);
  const after = tree(outputRoot);
  if (after.size !== expected.size) fail();
  for (const [relative, content] of after) if (!expected.get(relative)?.equals(content)) fail();
  for (const [target, original] of observedTargets) if (!read(target).equals(original)) fail();
  return { projectionDigest: projection.projection_digest, generatedCount: generated.size };
}

export function prepareWorkspaceRuntime(configuration, outputRoot) {
  try { return prepare(configuration, outputRoot); }
  catch {
    const error = new Error('workspace-export-preparation-failed');
    error.stack = 'workspace-export-preparation-failed';
    throw error;
  }
}

// Private parent-owned isolated runner API, deliberately unavailable through
// direct generator argv, environment, or presence of a saved projection file.
export async function runPreparedGenerator(configuration, generator, raw) {
  const generators = new Map([
    ['platform/server/tsconfig.image.json', 'scripts/04.deploy/build-platform-shell-image/prepare-runtime.mjs'],
    ['platform/server/tsconfig.runtime-test.json', 'platform/server/tests/run-runtime-tests.mjs'],
    ['products/kanbien-platform/tsconfig.runtime-test.json', 'products/kanbien-platform/tests/run-runtime-tests.mjs'],
  ]);
  if (process.argv.length !== 2 || preparedInput !== null || generators.get(configuration) !== generator
      || !Buffer.isBuffer(raw) || raw.length > MAX_BYTES) fail();
  preparedInput = {configuration, raw};
  await import(pathToFileURL(path.resolve(generator)).href);
  if (preparedInput !== null) fail();
}
