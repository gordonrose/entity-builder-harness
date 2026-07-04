#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.export.smoke-test
#   version: 1
#   status: active
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

echo "chat export smoke test passed."
