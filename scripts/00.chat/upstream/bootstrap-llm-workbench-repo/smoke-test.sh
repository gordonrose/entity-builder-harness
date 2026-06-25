#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.upstream.bootstrap-llm-workbench-repo.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test the llm-workbench bootstrap dry-run planner.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.upstream.bootstrap-llm-workbench-repo.readme
#     path: scripts/00.chat/upstream/bootstrap-llm-workbench-repo/README.md
#   - id: chat.script.bootstrap.audit-chat-bootstrap-file-set
#     path: scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
#   effects:
#   - writes-files

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

run_apply() {
  local repo="$1"
  local output="$2"
  bash "$SCRIPT" --target "$repo" --apply > "$output"
}

EMPTY_REPO="$TMP_ROOT/empty"
make_repo "$EMPTY_REPO"
run_plan "$EMPTY_REPO" "$TMP_ROOT/empty.out"
grep -q '^CREATE package.json$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan package creation"
grep -q '^CREATE scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan upstream planner script"
grep -q '^CREATE docs/00.chat/public-chat-workbench-adrs.md$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan public ADR manifest"
grep -q '^CREATE docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md$' "$TMP_ROOT/empty.out" || fail "empty repo did not plan selected chat ADR"
if grep -q '^CREATE docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md$' "$TMP_ROOT/empty.out"; then
  fail "empty repo planned historical non-public ADR"
fi
if grep -q '^CREATE docs/harness/architecture/adrs/0016-add-aws-layer.md$' "$TMP_ROOT/empty.out"; then
  fail "empty repo planned non-chat AWS ADR"
fi
grep -q '^conflicts: 0$' "$TMP_ROOT/empty.out" || fail "empty repo reported conflicts"
run_apply "$EMPTY_REPO" "$TMP_ROOT/empty-apply.out"
test -f "$EMPTY_REPO/AGENTS.md" || fail "apply did not create AGENTS.md"
test -f "$EMPTY_REPO/package.json" || fail "apply did not create package.json"
test -f "$EMPTY_REPO/scripts/00.chat/upstream/bootstrap-llm-workbench-repo/script.sh" || fail "apply did not create planner script"
test -f "$EMPTY_REPO/docs/harness/architecture/adrs/0013-create-chat-layer-and-on-demand-session-summary.md" || fail "apply did not create selected chat ADR"
test ! -e "$EMPTY_REPO/docs/harness/architecture/adrs/0001-record-harness-session-decisions-before-commit.md" || fail "apply created historical non-public ADR"
test ! -e "$EMPTY_REPO/docs/harness/architecture/adrs/0016-add-aws-layer.md" || fail "apply created non-chat AWS ADR"
node -e "const p=require(process.argv[1]); if (p.name !== 'llm-workbench') process.exit(1); if (!p.scripts.chat) process.exit(1)" "$EMPTY_REPO/package.json" || fail "created package.json did not match template"

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
run_apply "$PACKAGE_REPO" "$TMP_ROOT/package-apply.out"
node -e "const p=require(process.argv[1]); if (p.name !== 'existing-target') process.exit(1); if (p.scripts.build !== 'echo build') process.exit(1); if (!p.scripts['chat:new']) process.exit(1); if (!p.dependencies['left-pad']) process.exit(1)" "$PACKAGE_REPO/package.json" || fail "package merge did not preserve existing data and add chat scripts"

PRESERVE_REPO="$TMP_ROOT/preserve"
make_repo "$PRESERVE_REPO"
mkdir -p "$PRESERVE_REPO/scripts/shared/custom"
printf '#!/usr/bin/env bash\n' > "$PRESERVE_REPO/scripts/shared/custom/tool.sh"
run_plan "$PRESERVE_REPO" "$TMP_ROOT/preserve.out"
grep -q '^PRESERVE scripts/shared/custom/tool.sh$' "$TMP_ROOT/preserve.out" || fail "target-owned shared script was not preserved"
grep -q '^conflicts: 0$' "$TMP_ROOT/preserve.out" || fail "preserve repo reported conflicts"
run_apply "$PRESERVE_REPO" "$TMP_ROOT/preserve-apply.out"
test -f "$PRESERVE_REPO/scripts/shared/custom/tool.sh" || fail "apply removed target-owned shared script"
test -f "$PRESERVE_REPO/scripts/01.harness/run-governed-script.sh" || fail "apply did not create shared harness script"

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
if run_apply "$CONFLICT_REPO" "$TMP_ROOT/conflict-apply.out"; then
  fail "conflicting package script did not fail apply"
fi
test ! -e "$CONFLICT_REPO/AGENTS.md" || fail "conflicting apply wrote files before refusing"

echo "llm-workbench bootstrap planner/apply smoke test passed."
