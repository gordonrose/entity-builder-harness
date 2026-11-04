#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.export.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-07-03"
#   updated_on: "2026-10-31"
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test full and changed-files chat worktree exports.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.export.create-worktree-bundle
#     path: scripts/00.chat/export/create-worktree-bundle/script.js
#   - id: chat.checklists.llm-workbench-public-beta
#     path: .agentic/00.chat/checklists/llm-workbench-public-beta.md
#   effects:
#   - writes-files
#   - branches

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

require_entry() {
  local pattern="$1"
  local list_file="$2"

  grep -Eq -- "$pattern" "$list_file" || fail "missing zip entry matching: $pattern"
}

reject_entry() {
  local pattern="$1"
  local list_file="$2"

  if grep -Eq -- "$pattern" "$list_file"; then
    fail "unexpected zip entry matching: $pattern"
  fi
}

inspect_zip() {
  local zip_path="$1"
  local list_path="$2"
  local manifest_path="$3"

  node - "$zip_path" "$list_path" "$manifest_path" <<'NODE'
const fs = require('fs');

const zipPath = process.argv[2];
const listPath = process.argv[3];
const manifestPath = process.argv[4];
const data = fs.readFileSync(zipPath);

function fail(message) {
  console.error(message);
  process.exit(1);
}

let eocd = -1;
for (let offset = data.length - 22; offset >= 0; offset -= 1) {
  if (data.readUInt32LE(offset) === 0x06054b50) {
    eocd = offset;
    break;
  }
}

if (eocd < 0) {
  fail('missing zip end-of-central-directory record');
}

const totalEntries = data.readUInt16LE(eocd + 10);
const centralOffset = data.readUInt32LE(eocd + 16);
const entries = [];
let offset = centralOffset;

for (let index = 0; index < totalEntries; index += 1) {
  if (data.readUInt32LE(offset) !== 0x02014b50) {
    fail('invalid central-directory header');
  }
  const compressedSize = data.readUInt32LE(offset + 20);
  const nameLength = data.readUInt16LE(offset + 28);
  const extraLength = data.readUInt16LE(offset + 30);
  const commentLength = data.readUInt16LE(offset + 32);
  const localOffset = data.readUInt32LE(offset + 42);
  const name = data.subarray(offset + 46, offset + 46 + nameLength).toString('utf8');
  entries.push({ name, compressedSize, localOffset });
  offset += 46 + nameLength + extraLength + commentLength;
}

fs.writeFileSync(listPath, `${entries.map((entry) => entry.name).sort().join('\n')}\n`);

const manifestEntry = entries.find((entry) => entry.name.endsWith('/llm-workbench-export-manifest.json'));
if (!manifestEntry) {
  fail('missing export manifest');
}

const localOffset = manifestEntry.localOffset;
if (data.readUInt32LE(localOffset) !== 0x04034b50) {
  fail('invalid local file header for manifest');
}
const nameLength = data.readUInt16LE(localOffset + 26);
const extraLength = data.readUInt16LE(localOffset + 28);
const start = localOffset + 30 + nameLength + extraLength;
fs.writeFileSync(
  manifestPath,
  data.subarray(start, start + manifestEntry.compressedSize),
);
NODE
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/chat-export-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/scripts/00.chat/export/create-worktree-bundle" \
  "$REPO/scripts/00.chat/export/worktree" \
  "$REPO/scripts/00.chat/export/worktree-diff"

git -C "$REPO" init --quiet --initial-branch=main
git -C "$REPO" config user.name "chat export smoke"
git -C "$REPO" config user.email "chat-export-smoke@example.invalid"

cp "$SOURCE_ROOT/scripts/00.chat/export/create-worktree-bundle/script.js" \
  "$REPO/scripts/00.chat/export/create-worktree-bundle/script.js"
cp "$SOURCE_ROOT/scripts/00.chat/export/worktree/script.sh" \
  "$REPO/scripts/00.chat/export/worktree/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/export/worktree-diff/script.sh" \
  "$REPO/scripts/00.chat/export/worktree-diff/script.sh"
chmod +x \
  "$REPO/scripts/00.chat/export/worktree/script.sh" \
  "$REPO/scripts/00.chat/export/worktree-diff/script.sh"

printf '*.log\n' > "$REPO/.gitignore"
printf 'base readme\n' > "$REPO/README.md"
printf 'stable base\n' > "$REPO/stable.txt"
printf 'remove me\n' > "$REPO/removed.txt"
git -C "$REPO" add .gitignore README.md stable.txt removed.txt scripts
git -C "$REPO" commit --quiet -m "base"

git -C "$REPO" switch --quiet -c chat/export-smoke
printf 'changed readme\n' > "$REPO/README.md"
printf 'branch file\n' > "$REPO/committed.txt"
git -C "$REPO" rm --quiet removed.txt
git -C "$REPO" add README.md committed.txt
git -C "$REPO" commit --quiet -m "branch changes"

printf 'working tree edit\n' > "$REPO/stable.txt"
printf 'staged file\n' > "$REPO/staged.txt"
git -C "$REPO" add staged.txt
printf 'untracked file\n' > "$REPO/untracked.txt"
printf 'ignored file\n' > "$REPO/ignored.log"

bash "$REPO/scripts/00.chat/export/worktree/script.sh" \
  --output "$TMP_ROOT/full.zip" \
  "$REPO" > "$TMP_ROOT/full.out"
bash "$REPO/scripts/00.chat/export/worktree-diff/script.sh" \
  --base main \
  --output "$TMP_ROOT/diff.zip" \
  "$REPO" > "$TMP_ROOT/diff.out"

test -f "$TMP_ROOT/full.zip" || fail "full export zip was not created"
test -f "$TMP_ROOT/diff.zip" || fail "diff export zip was not created"

inspect_zip "$TMP_ROOT/full.zip" "$TMP_ROOT/full-list.txt" "$TMP_ROOT/full-manifest.json"
inspect_zip "$TMP_ROOT/diff.zip" "$TMP_ROOT/diff-list.txt" "$TMP_ROOT/diff-manifest.json"

require_entry '/README\.md$' "$TMP_ROOT/full-list.txt"
require_entry '/stable\.txt$' "$TMP_ROOT/full-list.txt"
require_entry '/committed\.txt$' "$TMP_ROOT/full-list.txt"
require_entry '/staged\.txt$' "$TMP_ROOT/full-list.txt"
require_entry '/untracked\.txt$' "$TMP_ROOT/full-list.txt"
reject_entry 'ignored\.log$' "$TMP_ROOT/full-list.txt"
reject_entry '(^|/)\.git(/|$)' "$TMP_ROOT/full-list.txt"

require_entry '/README\.md$' "$TMP_ROOT/diff-list.txt"
require_entry '/stable\.txt$' "$TMP_ROOT/diff-list.txt"
require_entry '/committed\.txt$' "$TMP_ROOT/diff-list.txt"
require_entry '/staged\.txt$' "$TMP_ROOT/diff-list.txt"
require_entry '/untracked\.txt$' "$TMP_ROOT/diff-list.txt"
reject_entry '/\.gitignore$' "$TMP_ROOT/diff-list.txt"
reject_entry 'ignored\.log$' "$TMP_ROOT/diff-list.txt"
reject_entry '(^|/)\.git(/|$)' "$TMP_ROOT/diff-list.txt"

grep -q '"kind": "worktree"' "$TMP_ROOT/full-manifest.json" \
  || fail "full manifest kind is wrong"
grep -q '"kind": "worktree-diff"' "$TMP_ROOT/diff-manifest.json" \
  || fail "diff manifest kind is wrong"
grep -q '"base_ref": "main"' "$TMP_ROOT/diff-manifest.json" \
  || fail "diff manifest is missing base ref"
grep -q '"removed.txt"' "$TMP_ROOT/diff-manifest.json" \
  || fail "diff manifest is missing deleted file"
grep -q '"untracked.txt"' "$TMP_ROOT/diff-manifest.json" \
  || fail "diff manifest is missing untracked file"

node - "$SOURCE_ROOT" "$TMP_ROOT" <<'NODE'
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const source = process.argv[2];
const temporary = process.argv[3];
const fixture = path.join(temporary, 'diagnostic-ports');
fs.mkdirSync(fixture);
fs.writeFileSync(path.join(fixture, 'tracked.txt'), 'intentional exported content');
fs.writeFileSync(path.join(fixture, 'package.json'), JSON.stringify({ version: '1.0.0', scripts: {} }));
fs.writeFileSync(path.join(fixture, 'actions.tsv'), '');
fs.writeFileSync(path.join(fixture, 'package.out'), '');
const session = '2026-06-18-00-00-diagnostics';
const sessionRelative = `commitLogs/2026/jun/18/${session}/README.md`;
fs.mkdirSync(path.dirname(path.join(fixture, sessionRelative)), { recursive: true });
fs.writeFileSync(path.join(fixture, sessionRelative), `<!-- agentic-session\nid: ${session}\nbranch: chat/${session}\n-->\n`);
const hook = path.join(temporary, 'diagnostic-ports.cjs');
fs.writeFileSync(hook, `(${function preload() {
  const fs = require('node:fs');
  const path = require('node:path');
  const cp = require('node:child_process');
  const root = process.env.DIAGNOSTIC_FIXTURE_ROOT;
  const mode = process.env.DIAGNOSTIC_FIXTURE_MODE;
  const kind = process.env.DIAGNOSTIC_FIXTURE_KIND;
  const output = process.env.DIAGNOSTIC_FIXTURE_OUTPUT;
  const calls = [];
  const original = { exists: fs.existsSync, read: fs.readFileSync, write: fs.writeFileSync, readdir: fs.readdirSync, mkdir: fs.mkdirSync, lstat: fs.lstatSync, readlink: fs.readlinkSync, log: console.log };
  const privateError = () => new Error('PRIVATE_IMPORTED_CANARY native path argv stderr');
  process.on('exit', () => original.write(process.env.DIAGNOSTIC_FIXTURE_CALLS, JSON.stringify(calls)));
  if (kind === 'workbench') {
    fs.existsSync = function (file) {
      const value = String(file);
      if (mode === 'session-read' && value.endsWith('/2026-06-18-00-00-diagnostics/README.md')) return false;
      if (value.startsWith(root) && (value.includes('/.llm-workbench/') || value.includes('/scripts/00.chat/'))) return true;
      if (mode === 'session-read' && value.endsWith('/commitLogs/2026/jun/18')) return true;
      return original.exists.apply(this, arguments);
    };
  }
  fs.readdirSync = function (file) {
    if ((mode === 'session-read' && String(file).endsWith('/commitLogs/2026/jun/18')) || mode === 'ownership-discovery') throw privateError();
    return original.readdir.apply(this, arguments);
  };
  fs.readFileSync = function (file) {
    const value = String(file);
    if (mode === 'bundle-read' && value === path.join(root, 'tracked.txt')) throw privateError();
    if (mode === 'ownership-json' && value === path.join(root, '.llm-workbench/manifest.json')) return '{PRIVATE_IMPORTED_CANARY';
    return original.read.apply(this, arguments);
  };
  fs.lstatSync = function (file) {
    if (mode === 'bundle-link' && String(file) === path.join(root, 'tracked.txt')) return { isSymbolicLink: () => true };
    return original.lstat.apply(this, arguments);
  };
  fs.readlinkSync = function (file) {
    if (mode === 'bundle-link' && String(file) === path.join(root, 'tracked.txt')) throw privateError();
    return original.readlink.apply(this, arguments);
  };
  fs.mkdirSync = function (directory) {
    if (mode === 'bundle-directory' && String(directory) === path.dirname(output)) throw privateError();
    return original.mkdir.apply(this, arguments);
  };
  fs.writeFileSync = function (file) {
    const value = String(file);
    if (mode === 'bundle-write-before' && value === output) throw privateError();
    if (mode === 'bundle-write-after' && value === output) { original.write.apply(this, arguments); throw privateError(); }
    if ((mode === 'ownership-state' || mode === 'ownership-apply') && value === path.join(root, '.llm-workbench/manifest.json')) throw privateError();
    return original.write.apply(this, arguments);
  };
  console.log = function () {
    if (mode === 'bundle-report') throw privateError();
    return original.log.apply(this, arguments);
  };
  cp.spawnSync = function (command, args, options) {
    calls.push({ command, args, options: { stdio: options.stdio, encoding: options.encoding, cwd: options.cwd } });
    const op = args[2];
    const answer = { status: 0, stdout: '', stderr: '', signal: null };
    if (command === 'git' && op === 'rev-parse') answer.stdout = args.includes('--show-toplevel') ? root + '\n' : 'a'.repeat(40) + '\n';
    if (command === 'git' && op === 'branch') answer.stdout = kind === 'workbench' ? 'chat/2026-06-18-00-00-diagnostics\n' : 'main\n';
    if (command === 'git' && op === 'ls-files' && !args.includes('--others')) answer.stdout = 'tracked.txt\0';
    if (command === 'git' && op === 'diff') answer.status = 1;
    if (kind === 'bundle' && (mode === 'bundle-git-root' ? args.includes('--show-toplevel') : op === 'ls-files') && ['bundle-git-root', 'bundle-git', 'bundle-git-threw'].includes(mode)) {
      if (mode === 'bundle-git-threw') throw privateError();
      return { status: 23, stdout: 'PRIVATE_IMPORTED_CANARY', stderr: 'PRIVATE_IMPORTED_CANARY' };
    }
    if (kind === 'workbench' && op === 'branch' && mode.startsWith('capture-')) {
      if (mode === 'capture-threw') throw privateError();
      if (mode === 'capture-error') return { status: null, error: privateError() };
      if (mode === 'capture-signal') return { status: null, signal: 'PRIVATE_IMPORTED_CANARY', stderr: 'PRIVATE_IMPORTED_CANARY' };
      return { status: 23, stdout: 'PRIVATE_IMPORTED_CANARY', stderr: 'PRIVATE_IMPORTED_CANARY' };
    }
    if (kind === 'workbench' && command === 'bash' && mode.startsWith('run-')) {
      if (mode === 'run-error') return { status: null, error: privateError() };
      if (mode === 'run-signal') return { status: null, signal: 'PRIVATE_IMPORTED_CANARY' };
      return { status: 17 };
    }
    if (kind === 'workbench' && op === 'diff' && mode === 'staged-error') return { status: null, error: privateError() };
    if (kind === 'workbench' && op === 'commit' && ['commit-error', 'commit-threw', 'commit-status'].includes(mode)) {
      if (mode === 'commit-threw') throw privateError();
      return mode === 'commit-error' ? { status: null, error: privateError() } : { status: 19 };
    }
    if (kind === 'workbench' && op === 'rev-parse' && args.includes('HEAD') && mode === 'identity-failed') return { status: 17, stderr: 'PRIVATE_IMPORTED_CANARY' };
    if (kind === 'workbench' && command === 'bash' && ((mode === 'record-error' && args[0].includes('/record-chat-commit/')) || (mode === 'checkpoint-error' && args[0].includes('/checkpoint-chat-session-log/')))) return { status: null, error: privateError() };
    return answer;
  };
}.toString()})();\n`);

function invoke(kind, mode, relative, args) {
  const output = path.join(temporary, `${kind}-${mode}.zip`);
  const callFile = path.join(temporary, `${kind}-${mode}.calls.json`);
  const selectedArgs = args.map((value) => value === '<output>' ? output : value);
  const result = spawnSync(process.execPath, ['--require', hook, path.join(source, relative), ...selectedArgs], {
    cwd: fixture, encoding: 'utf8', env: { ...process.env, DIAGNOSTIC_FIXTURE_ROOT: fixture, DIAGNOSTIC_FIXTURE_MODE: mode, DIAGNOSTIC_FIXTURE_KIND: kind, DIAGNOSTIC_FIXTURE_OUTPUT: output, DIAGNOSTIC_FIXTURE_CALLS: callFile },
  });
  assert.equal(result.error, undefined);
  assert.ok(!`${result.stdout}${result.stderr}`.includes('PRIVATE_IMPORTED_CANARY'), `${kind}/${mode} disclosed private evidence`);
  return { ...result, calls: JSON.parse(fs.readFileSync(callFile, 'utf8')), output };
}
const bundle = 'scripts/00.chat/export/create-worktree-bundle/script.js';
const cli = 'bin/llm-workbench.js';
const owner = 'bin/llm-workbench-ownership.js';
const bundleArgs = ['--mode', 'worktree', '--output', '<output>', fixture];
const good = invoke('bundle', 'good', bundle, bundleArgs);
assert.equal(good.status, 0); assert.equal(good.calls.length, 5); assert.ok(fs.existsSync(good.output));
assert.deepEqual(good.calls.map((item) => item.args.slice(2)), [['rev-parse', '--show-toplevel'], ['branch', '--show-current'], ['rev-parse', '--verify', 'HEAD'], ['ls-files', '-z'], ['ls-files', '--others', '--exclude-standard', '-z']]);
assert.ok(fs.readFileSync(good.output).includes(Buffer.from('intentional exported content')));
for (const [mode, phase, state, written] of [
  ['bundle-git', 'file-list-observation', 'not-reached', false],
  ['bundle-git-threw', 'file-list-observation', 'not-reached', false],
  ['bundle-read', 'file-entry-read', 'not-reached', false],
  ['bundle-link', 'file-entry-read', 'not-reached', false],
  ['bundle-directory', 'output-directory', 'not-reached', false],
  ['bundle-write-before', 'output-write', 'unknown', false],
  ['bundle-write-after', 'output-write', 'unknown', true],
  ['bundle-report', 'success-report', 'completed', true],
]) {
  const result = invoke('bundle', mode, bundle, bundleArgs);
  assert.equal(result.status, 1); assert.ok(result.stderr.includes(`phase=${phase}; archive-write=${state}`));
  assert.equal(fs.existsSync(result.output), written);
  assert.equal(result.calls.length, mode.startsWith('bundle-git') ? 4 : 5);
}
const rootFailure = invoke('bundle', 'bundle-git-root', bundle, bundleArgs);
assert.equal(rootFailure.status, 1); assert.equal(rootFailure.calls.length, 1);
assert.ok(rootFailure.stderr.includes('could not be confirmed')); assert.ok(!rootFailure.stderr.includes('not inside a Git'));
assert.equal(invoke('bundle', 'unknown-argument', bundle, ['--PRIVATE_IMPORTED_CANARY']).status, 2);

for (const mode of ['capture-failed', 'capture-error', 'capture-signal', 'capture-threw']) {
  const result = invoke('workbench', mode, cli, ['commit', '-m', 'PRIVATE_IMPORTED_CANARY']);
  assert.equal(result.status, 1); assert.equal(result.calls.length, 2);
  assert.ok(result.stderr.includes('phase=branch-observation;'));
}
for (const [mode, status, phase] of [['run-error', 1, 'command-list'], ['run-signal', 1, 'command-list'], ['run-status', 17, 'command-list']]) {
  const result = invoke('workbench', mode, cli, ['list']);
  assert.equal(result.status, status); assert.equal(result.calls.length, 2);
  if (phase) assert.ok(result.stderr.includes(`phase=${phase};`));
}
for (const [mode, status, phase] of [['commit-error', 1, 'task-commit'], ['commit-threw', 1, 'task-commit'], ['commit-status', 19, 'task-commit'], ['identity-failed', 1, 'commit-identity'], ['record-error', 1, 'commit-recording'], ['checkpoint-error', 1, 'session-checkpoint'], ['staged-error', 0, null]]) {
  const result = invoke('workbench', mode, cli, ['commit', '-m', 'PRIVATE_IMPORTED_CANARY']);
  assert.equal(result.status, status);
  const operations = result.calls.map((item) => item.command === 'git' ? item.args[2] : path.basename(path.dirname(item.args[0])));
  assert.deepEqual(operations.slice(0, 9), ['rev-parse', 'branch', 'check-write-location', 'check-commit-prerequisites', 'add', 'reset', 'diff', 'prepare-chat-session-before-commit', 'commit']);
  if (phase) assert.ok(result.stderr.includes(`phase=${phase};`));
  if (mode === 'identity-failed') { assert.equal(operations.length, 10); assert.ok(result.stderr.includes('effect=unknown')); }
  if (mode === 'staged-error') { assert.ok(result.stderr.includes('staged-observation-unavailable; effect=unknown')); assert.equal(operations.at(-1), 'checkpoint-chat-session-log'); }
}
const sessionFailure = invoke('workbench', 'session-read', cli, ['commit', '-m', 'message']);
assert.equal(sessionFailure.status, 1); assert.ok(sessionFailure.stderr.includes('phase=session-log-discovery;'));
for (const args of [['PRIVATE_IMPORTED_CANARY'], ['commit', '--PRIVATE_IMPORTED_CANARY'], ['init', '--PRIVATE_IMPORTED_CANARY'], ['adopt', '--PRIVATE_IMPORTED_CANARY'], ['sessions', 'PRIVATE_IMPORTED_CANARY'], ['merge-main', '--PRIVATE_IMPORTED_CANARY']]) assert.equal(invoke('workbench', `argument-${args[0]}`, cli, args).status, 2);

const ownership = require(path.join(source, owner));
assert.throws(() => ownership.planUpdate(fixture, path.join(temporary, 'missing-manifest')), (error) => error instanceof Error && error.message === 'llm-workbench manifest not found: .llm-workbench/manifest.json');
for (const [mode, args, condition] of [['unknown-argument', ['update', '--PRIVATE_IMPORTED_CANARY'], 'argument-unknown'], ['unknown-command', ['PRIVATE_IMPORTED_CANARY'], 'command-unknown'], ['target-required', ['update', '--target'], 'target-required'], ['mode-conflict', ['update', '--dry-run', '--apply'], 'mode-conflict']]) {
  const result = invoke('ownership', mode, owner, args);
  assert.equal(result.status, 1); assert.ok(result.stderr.includes(`phase=arguments; condition=${condition};`));
}
const missing = invoke('ownership', 'missing', owner, ['update', '--target', fixture]);
assert.equal(missing.status, 1); assert.ok(missing.stderr.includes('phase=update-plan; condition=manifest-not-found;'));
fs.mkdirSync(path.join(fixture, '.llm-workbench'));
fs.writeFileSync(path.join(fixture, '.llm-workbench/manifest.json'), JSON.stringify({ managed_files: [], managed_blocks: [], managed_package_scripts: [] }));
const malformed = invoke('ownership', 'ownership-json', owner, ['update', '--target', fixture]);
assert.equal(malformed.status, 1); assert.ok(malformed.stderr.includes('phase=update-plan; condition=native-boundary-threw;'));
const discovery = invoke('ownership', 'ownership-discovery', owner, ['adopt', '--target', fixture]);
assert.equal(discovery.status, 1); assert.ok(discovery.stderr.includes('phase=adoption-plan;'));
for (const [mode, args, phase] of [
  ['ownership-state', ['write-install-state', fixture, fixture, path.join(fixture, 'actions.tsv'), path.join(fixture, 'package.out')], 'install-state'],
  ['ownership-apply', ['update', '--apply', '--target', fixture], 'update-apply'],
]) {
  const result = invoke('ownership', mode, owner, args);
  assert.equal(result.status, 1); assert.ok(result.stderr.includes(`phase=${phase}; condition=native-boundary-threw; effect=unknown`));
  assert.ok(fs.existsSync(path.join(fixture, '.llm-workbench/lock.json')), 'earlier lock write was lost or falsely declared absent');
}
const retainedLock = fs.readFileSync(path.join(fixture, '.llm-workbench/lock.json'));
fs.writeFileSync(path.join(fixture, '.llm-workbench/manifest.json'), JSON.stringify({ managed_files: [{ path: 'bin/llm-workbench.js', sha256: 'old' }], managed_blocks: [], managed_package_scripts: [] }));
const blocked = invoke('ownership', 'ownership-blocked', owner, ['update', '--apply', '--target', fixture]);
assert.equal(blocked.status, 1); assert.ok(blocked.stderr.includes('condition=plan-blocked;'));
assert.deepEqual(fs.readFileSync(path.join(fixture, '.llm-workbench/lock.json')), retainedLock);
console.log('imported command/export diagnostic ports passed.');
NODE

echo "chat export smoke test passed."
