#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: shared-harness
#   purpose: Smoke test governed script runner allowlist and approval behavior.
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/harness/standards/governed-script-permissions.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: writes-files, commits

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/governed-script-runner.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/scripts/shared/chat" \
  "$REPO/scripts/shared/chat/request-initialization" \
  "$REPO/scripts/shared/git" \
  "$REPO/scripts/shared/harness" \
  "$REPO/scripts/local"

cp "$SOURCE_ROOT/scripts/shared/harness/run-governed-script.sh" \
  "$REPO/scripts/shared/harness/run-governed-script.sh"

make_fixture() {
  local path="$1"
  local label="$2"

  mkdir -p "$REPO/${path%/*}"
  {
    printf '#!/usr/bin/env bash\n'
    printf 'set -euo pipefail\n'
    printf 'echo "%s:$*"\n' "$label"
  } > "$REPO/$path"
}

make_fixture "scripts/shared/git/check-write-location.sh" "allowed-check"
make_fixture "scripts/shared/chat/ensure-llm-workbench-repo.sh" "allowed-workbench"
make_fixture "scripts/shared/chat/request-initialization/auto-start-missing-session.sh" "approved-auto-start"
make_fixture "scripts/shared/chat/rename-current-chat-log-folder.sh" "approved-action"
make_fixture "scripts/shared/git/cleanup-empty-chat-branches.sh" "dangerous-helper"
make_fixture "scripts/shared/harness/check-deterministic-process-drift.sh" "allowed-harness"
make_fixture "scripts/local/not-governed.sh" "local-script"

git -C "$REPO" init --quiet
git -C "$REPO" add scripts
git -C "$REPO" \
  -c user.name="Smoke Test" \
  -c user.email="smoke@example.invalid" \
  commit --quiet -m "fixture"

cd "$REPO"

OUT="$(bash scripts/shared/harness/run-governed-script.sh scripts/shared/git/check-write-location.sh arg1)"
if [ "$OUT" != "allowed-check:arg1" ]; then
  fail "allowed check did not run through the governed runner: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run >"$TMP_ROOT/workbench-missing.out" 2>&1; then
  fail "workbench clone helper ran without --approved-action"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run)"
if [ "$OUT" != "allowed-workbench:--dry-run" ]; then
  fail "allowed workbench helper did not run through the governed runner: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat" >"$TMP_ROOT/auto-start-missing.out" 2>&1; then
  fail "auto-start helper ran without --approved-action"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat")"
if [ "$OUT" != "approved-auto-start:new chat" ]; then
  fail "auto-start helper did not run with --approved-action: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/chat/rename-current-chat-log-folder.sh test >"$TMP_ROOT/approved-missing.out" 2>&1; then
  fail "approval-sensitive script ran without --approved-action"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/rename-current-chat-log-folder.sh test)"
if [ "$OUT" != "approved-action:test" ]; then
  fail "approval-sensitive script did not run with --approved-action: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/git/cleanup-empty-chat-branches.sh --apply >"$TMP_ROOT/dangerous.out" 2>&1; then
  fail "dangerous helper was allowed"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/local/not-governed.sh >"$TMP_ROOT/local.out" 2>&1; then
  fail "non-shared local script was allowed"
fi

if bash scripts/shared/harness/run-governed-script.sh ../scripts/shared/git/check-write-location.sh >"$TMP_ROOT/traversal.out" 2>&1; then
  fail "parent traversal path was allowed"
fi

if bash scripts/shared/harness/run-governed-script.sh /bin/echo >"$TMP_ROOT/absolute.out" 2>&1; then
  fail "absolute command path was allowed"
fi

LIST="$(bash scripts/shared/harness/run-governed-script.sh --list)"
case "$LIST" in
  *"always scripts/shared/git/check-write-location.sh"*)
    ;;
  *)
    fail "--list output did not include expected always entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/shared/chat/ensure-llm-workbench-repo.sh"*)
    ;;
  *)
    fail "--list output did not include expected workbench entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/shared/chat/request-initialization/auto-start-missing-session.sh"*)
    ;;
  *)
    fail "--list output did not include expected auto-start entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/shared/chat/rename-current-chat-log-folder.sh"*)
    ;;
  *)
    fail "--list output did not include expected approved entry"
    ;;
esac

echo "governed script runner smoke test passed"
