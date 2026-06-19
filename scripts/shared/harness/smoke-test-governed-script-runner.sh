#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Smoke test governed script runner allowlist and approval behavior.
#   domain: validation
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
  "$REPO/scripts/00.chat/session-log/rename-current-chat-log-folder" \
  "$REPO/scripts/00.chat/session-log/prepare-chat-session-before-commit" \
  "$REPO/scripts/00.chat/session-log/record-chat-commit" \
  "$REPO/scripts/00.chat/session-log/checkpoint-chat-session-log" \
  "$REPO/scripts/00.chat/startup/auto-start-missing-session" \
  "$REPO/scripts/00.chat/upstream/ensure-llm-workbench-repo" \
  "$REPO/scripts/00.chat/worktree/check-write-location" \
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
make_fixture "scripts/00.chat/worktree/check-write-location/script.sh" "canonical-check"
make_fixture "scripts/shared/chat/ensure-llm-workbench-repo.sh" "allowed-workbench"
make_fixture "scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh" "canonical-workbench"
make_fixture "scripts/shared/chat/request-initialization/auto-start-missing-session.sh" "approved-auto-start"
make_fixture "scripts/00.chat/startup/auto-start-missing-session/script.sh" "canonical-auto-start"
make_fixture "scripts/shared/chat/rename-current-chat-log-folder.sh" "approved-action"
make_fixture "scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh" "canonical-approved-action"
make_fixture "scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh" "canonical-prepare"
make_fixture "scripts/00.chat/session-log/record-chat-commit/script.sh" "canonical-record"
make_fixture "scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh" "canonical-checkpoint"
make_fixture "scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "dangerous-helper"
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

OUT="$(bash scripts/shared/harness/run-governed-script.sh scripts/00.chat/worktree/check-write-location/script.sh arg1)"
if [ "$OUT" != "canonical-check:arg1" ]; then
  fail "canonical allowed check did not run through the governed runner: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run >"$TMP_ROOT/workbench-missing.out" 2>&1; then
  fail "workbench clone helper ran without --approved-action"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run)"
if [ "$OUT" != "allowed-workbench:--dry-run" ]; then
  fail "allowed workbench helper did not run through the governed runner: $OUT"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh --dry-run)"
if [ "$OUT" != "canonical-workbench:--dry-run" ]; then
  fail "canonical workbench helper did not run through the governed runner: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat" >"$TMP_ROOT/auto-start-missing.out" 2>&1; then
  fail "auto-start helper ran without --approved-action"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat")"
if [ "$OUT" != "approved-auto-start:new chat" ]; then
  fail "auto-start helper did not run with --approved-action: $OUT"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/00.chat/startup/auto-start-missing-session/script.sh "new chat")"
if [ "$OUT" != "canonical-auto-start:new chat" ]; then
  fail "canonical auto-start helper did not run with --approved-action: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/shared/chat/rename-current-chat-log-folder.sh test >"$TMP_ROOT/approved-missing.out" 2>&1; then
  fail "approval-sensitive script ran without --approved-action"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/shared/chat/rename-current-chat-log-folder.sh test)"
if [ "$OUT" != "approved-action:test" ]; then
  fail "approval-sensitive script did not run with --approved-action: $OUT"
fi

OUT="$(bash scripts/shared/harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh test)"
if [ "$OUT" != "canonical-approved-action:test" ]; then
  fail "canonical approval-sensitive script did not run with --approved-action: $OUT"
fi

if bash scripts/shared/harness/run-governed-script.sh scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply >"$TMP_ROOT/dangerous.out" 2>&1; then
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
  *"always scripts/00.chat/worktree/check-write-location/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical always entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical workbench entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/startup/auto-start-missing-session/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical auto-start entry"
    ;;
esac

case "$LIST" in
  *"approved scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical approved entry"
    ;;
esac

echo "governed script runner smoke test passed"
