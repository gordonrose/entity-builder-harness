#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test the llm-workbench bootstrap dry-run planner.
#   domain: validation
#   portability: llm-workbench-validation
#   used_by:
#     - scripts/00.chat/upstream/bootstrap-llm-workbench-repo/README.md
#     - scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
#   effects: writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$SOURCE_ROOT/scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/llm-workbench-bootstrap-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

make_repo() {
  local repo="$1"
  mkdir -p "$repo"
  git -C "$repo" init --quiet --initial-branch=main
}

run_plan() {
  local repo="$1"
  local output="$2"
  bash "$SCRIPT" --target "$repo" --dry-run > "$output"
}

EMPTY_REPO="$TMP_ROOT/empty"
make_repo "$EMPTY_REPO"
run_plan "$EMPTY_REPO" "$TMP_ROOT/empty.out"
grep -q '^CREATE package.json$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan package creation"
grep -q '^CREATE scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan upstream planner script"
grep -q '^conflicts: 0$' "$TMP_ROOT/empty.out" || fail "empty repo reported conflicts"

PACKAGE_REPO="$TMP_ROOT/package"
make_repo "$PACKAGE_REPO"
cat > "$PACKAGE_REPO/package.json" <<'JSON'
{
  "name": "existing-target",
  "scripts": {
    "build": "echo build"
  },
  "dependencies": {
    "left-pad": "1.3.0"
  }
}
JSON
run_plan "$PACKAGE_REPO" "$TMP_ROOT/package.out"
grep -q '^PACKAGE_ADD_SCRIPT chat ' "$TMP_ROOT/package.out" || fail "existing package did not plan chat script add"
grep -q '^PACKAGE_PRESERVE_SCRIPT build echo build$' "$TMP_ROOT/package.out" || fail "existing package did not preserve unrelated script"
grep -q '^conflicts: 0$' "$TMP_ROOT/package.out" || fail "existing package reported conflicts"

PRESERVE_REPO="$TMP_ROOT/preserve"
make_repo "$PRESERVE_REPO"
mkdir -p "$PRESERVE_REPO/scripts/shared/custom"
printf '#!/usr/bin/env bash\n' > "$PRESERVE_REPO/scripts/shared/custom/tool.sh"
run_plan "$PRESERVE_REPO" "$TMP_ROOT/preserve.out"
grep -q '^PRESERVE scripts/shared/custom/tool.sh$' "$TMP_ROOT/preserve.out" || fail "target-owned shared script was not preserved"
grep -q '^conflicts: 0$' "$TMP_ROOT/preserve.out" || fail "preserve repo reported conflicts"

CONFLICT_REPO="$TMP_ROOT/conflict"
make_repo "$CONFLICT_REPO"
cat > "$CONFLICT_REPO/package.json" <<'JSON'
{
  "name": "conflict-target",
  "scripts": {
    "chat:new": "echo not-the-workbench"
  }
}
JSON
if run_plan "$CONFLICT_REPO" "$TMP_ROOT/conflict.out"; then
  fail "conflicting package script did not fail dry-run"
fi
grep -q '^PACKAGE_CONFLICT_SCRIPT chat:new ' "$TMP_ROOT/conflict.out" || fail "conflicting package script was not reported"
grep -q '^package_conflicts: yes$' "$TMP_ROOT/conflict.out" || fail "package conflict summary missing"

echo "llm-workbench bootstrap planner smoke test passed."
