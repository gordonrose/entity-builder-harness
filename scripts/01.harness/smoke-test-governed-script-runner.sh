#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.smoke-test-governed-script-runner
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test governed script runner allowlist and approval behavior.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: harness.standards.governed-script-permissions
#     path: .agentic/01.harness/standards/governed-script-permissions.md
#   - id: harness.script.run-governed-script
#     path: scripts/01.harness/run-governed-script.sh
#   effects:
#   - commits
#   - writes-files

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
  "$REPO/scripts/00.chat/startup/resolve-current-chat-session" \
  "$REPO/scripts/00.chat/upstream/ensure-llm-workbench-repo" \
  "$REPO/scripts/00.chat/worktree/check-write-location" \
  "$REPO/scripts/02.rag-rulebook/run-local-service" \
  "$REPO/scripts/01.harness" \
  "$REPO/scripts/local"

cp "$SOURCE_ROOT/scripts/01.harness/run-governed-script.sh" \
  "$REPO/scripts/01.harness/run-governed-script.sh"

make_fixture() {
  local path="$1"
  local label="$2"
  local effects="${3:-read-only}"
  local effect

  mkdir -p "$REPO/${path%/*}"
  {
    printf '#!/usr/bin/env bash\n'
    printf 'set -euo pipefail\n'
    printf '\n'
    printf '# agentic-artifact:\n'
    printf '#   schema: agentic-artifact/v2\n'
    printf '#   id: smoke.fixture.%s\n' "$(printf '%s' "$label" | tr -c '[:alnum:]' '-')"
    printf '#   version: 1\n'
    printf '#   status: active\n'
    printf '#   layer: 00.chat\n'
    printf '#   domain: smoke-test\n'
    printf '#   disciplines:\n'
    printf '#   - agentic\n'
    printf '#   kind: script\n'
    printf '#   purpose: Fixture script for governed runner smoke tests.\n'
    printf '#   effects:\n'
    for effect in $effects; do
      printf '#   - %s\n' "$effect"
    done
    printf '\n'
    printf 'echo "%s:$*"\n' "$label"
  } > "$REPO/$path"
}

make_fixture "scripts/shared/git/check-write-location.sh" "retired-check"
make_fixture "scripts/00.chat/worktree/check-write-location/script.sh" "canonical-check"
make_fixture "scripts/shared/chat/ensure-llm-workbench-repo.sh" "retired-workbench" "writes-files"
make_fixture "scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh" "canonical-workbench" "writes-files"
make_fixture "scripts/shared/chat/request-initialization/auto-start-missing-session.sh" "retired-auto-start" "writes-files"
make_fixture "scripts/00.chat/startup/auto-start-missing-session/script.sh" "canonical-auto-start" "writes-files"
make_fixture "scripts/00.chat/startup/resolve-current-chat-session/script.sh" "canonical-resolve-session" "writes-files"
make_fixture "scripts/shared/chat/rename-current-chat-log-folder.sh" "retired-rename" "writes-files"
make_fixture "scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh" "canonical-approved-action" "writes-files"
make_fixture "scripts/00.chat/session-log/prepare-chat-session-before-commit/script.sh" "canonical-prepare" "writes-files"
make_fixture "scripts/00.chat/session-log/record-chat-commit/script.sh" "canonical-record" "writes-files commits"
make_fixture "scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh" "canonical-checkpoint" "writes-files"
make_fixture "scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "dangerous-helper" "branches destructive writes-files"
make_fixture "scripts/01.harness/check-deterministic-process-drift.sh" "allowed-harness"
make_fixture "scripts/02.rag-rulebook/run-local-service/smoke-test.sh" "canonical-rag-smoke" "writes-files network"
make_fixture "scripts/local/not-governed.sh" "local-script"

git -C "$REPO" init --quiet
git -C "$REPO" add scripts
git -C "$REPO" \
  -c user.name="Smoke Test" \
  -c user.email="smoke@example.invalid" \
  commit --quiet -m "fixture"

cd "$REPO"

if bash scripts/01.harness/run-governed-script.sh scripts/shared/git/check-write-location.sh arg1 >"$TMP_ROOT/check-retired.out" 2>&1; then
  fail "retired check-write-location helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh scripts/00.chat/worktree/check-write-location/script.sh arg1)"
if [ "$OUT" != "canonical-check:arg1" ]; then
  fail "canonical allowed check did not run through the governed runner: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run >"$TMP_ROOT/workbench-missing.out" 2>&1; then
  fail "workbench clone helper ran without --approved-action"
fi

if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/shared/chat/ensure-llm-workbench-repo.sh --dry-run >"$TMP_ROOT/workbench-retired.out" 2>&1; then
  fail "retired workbench helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh --dry-run)"
if [ "$OUT" != "canonical-workbench:--dry-run" ]; then
  fail "canonical workbench helper did not run through the governed runner: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat" >"$TMP_ROOT/auto-start-missing.out" 2>&1; then
  fail "auto-start helper ran without --approved-action"
fi

if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/shared/chat/request-initialization/auto-start-missing-session.sh "new chat" >"$TMP_ROOT/auto-start-retired.out" 2>&1; then
  fail "retired auto-start helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/auto-start-missing-session/script.sh "new chat")"
if [ "$OUT" != "canonical-auto-start:new chat" ]; then
  fail "canonical auto-start helper did not run with --approved-action: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/00.chat/startup/resolve-current-chat-session/script.sh "new chat" >"$TMP_ROOT/resolve-missing.out" 2>&1; then
  fail "startup resolver ran without --approved-action"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/startup/resolve-current-chat-session/script.sh "new chat")"
if [ "$OUT" != "canonical-resolve-session:new chat" ]; then
  fail "startup resolver did not run with --approved-action: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/shared/chat/rename-current-chat-log-folder.sh test >"$TMP_ROOT/approved-missing.out" 2>&1; then
  fail "approval-sensitive script ran without --approved-action"
fi

if bash scripts/01.harness/run-governed-script.sh --approved-action scripts/shared/chat/rename-current-chat-log-folder.sh test >"$TMP_ROOT/rename-retired.out" 2>&1; then
  fail "retired rename helper was still accepted"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh test)"
if [ "$OUT" != "canonical-approved-action:test" ]; then
  fail "canonical approval-sensitive script did not run with --approved-action: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/02.rag-rulebook/run-local-service/smoke-test.sh >"$TMP_ROOT/rag-smoke-missing.out" 2>&1; then
  fail "RAG service smoke test ran without --approved-action"
fi

OUT="$(bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/run-local-service/smoke-test.sh)"
if [ "$OUT" != "canonical-rag-smoke:" ]; then
  fail "canonical RAG service smoke test did not run through the governed runner: $OUT"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply >"$TMP_ROOT/dangerous.out" 2>&1; then
  fail "dangerous helper was allowed"
fi

if bash scripts/01.harness/run-governed-script.sh scripts/local/not-governed.sh >"$TMP_ROOT/local.out" 2>&1; then
  fail "non-shared local script was allowed"
fi

if bash scripts/01.harness/run-governed-script.sh ../scripts/shared/git/check-write-location.sh >"$TMP_ROOT/traversal.out" 2>&1; then
  fail "parent traversal path was allowed"
fi

if bash scripts/01.harness/run-governed-script.sh /bin/echo >"$TMP_ROOT/absolute.out" 2>&1; then
  fail "absolute command path was allowed"
fi

LIST="$(bash scripts/01.harness/run-governed-script.sh --list)"
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
  *"approved scripts/00.chat/startup/resolve-current-chat-session/script.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical startup resolver entry"
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

case "$LIST" in
  *"approved scripts/02.rag-rulebook/run-local-service/smoke-test.sh"*)
    ;;
  *)
    fail "--list output did not include expected canonical RAG smoke test entry"
    ;;
esac

case "$LIST" in
  *"scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"*)
    fail "--list output included never-persistent destructive helper"
    ;;
esac

echo "governed script runner smoke test passed"
