#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.main-refresh.classify-refresh-readiness.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-06-17"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: main-refresh
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test refresh-readiness classification before main refresh.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-refresh-from-main
#     path: .agentic/00.chat/workflows/chat-refresh-from-main.md
#   - id: chat.script.main-refresh.classify-refresh-readiness
#     path: scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
#   effects:
#   - branches
#   - commits
#   - writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/main-refresh-classifier-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-06-17-00-00-test-chat"
SESSION_LOG="commitLogs/2026/jun/17/${SESSION_ID}/README.md"
OTHER_LOG="commitLogs/2026/jun/17/other-chat/README.md"

mkdir -p \
  "$REPO/scripts/00.chat/reporting/generate-commit-log-summary" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/$(dirname "$SESSION_LOG")" \
  "$REPO/$(dirname "$OTHER_LOG")"

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" \
  "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/reporting/generate-commit-log-summary/script.sh" \
  "$REPO/scripts/00.chat/reporting/generate-commit-log-summary/script.sh"
mkdir -p "$REPO/scripts/00.chat/main-refresh/classify-refresh-readiness"
cp "$SOURCE_ROOT/scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh" \
  "$REPO/scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh"
for capability in check-chat-is-current-with-main show-main-update-status rehearse-refresh-from-main; do
  mkdir -p "$REPO/scripts/00.chat/main-refresh/$capability"
  cp "$SOURCE_ROOT/scripts/00.chat/main-refresh/$capability/script.sh" \
    "$REPO/scripts/00.chat/main-refresh/$capability/script.sh"
done

git -C "$REPO" init -q -b main
git -C "$REPO" config user.name "Smoke Test"
git -C "$REPO" config user.email "smoke@example.invalid"

cat > "$REPO/README.md" <<'EOF'
base
EOF

cat > "$REPO/$SESSION_LOG" <<EOF
# Chat Session: ${SESSION_ID}

<!-- agentic-session
id: ${SESSION_ID}
chat_duration: 10s
estimated_chat_tokens: 50 tokens
-->
EOF

(
  cd "$REPO"
  bash scripts/00.chat/reporting/generate-commit-log-summary/script.sh --output "$TMP_ROOT/base-summary.md" >/dev/null
)

git -C "$REPO" add .
git -C "$REPO" commit -q -m "base"
git -C "$REPO" switch -q -c "chat/${SESSION_ID}"

classification() {
  (
    cd "$REPO"
    bash scripts/00.chat/main-refresh/classify-refresh-readiness/script.sh
  ) | sed -n 's/^classification=//p' | head -n 1
}

if [ "$(classification)" != "clean" ]; then
  fail "clean worktree was not classified as clean"
fi

cat > "$REPO/$OTHER_LOG" <<'EOF'
# Chat Session: other-chat

<!-- agentic-session
id: other-chat
chat_duration: 20s
estimated_chat_tokens: 75 tokens
-->
EOF

git -C "$REPO" add "$OTHER_LOG"
git -C "$REPO" commit -q -m "add other log"
printf '\nlocal note\n' >> "$REPO/$SESSION_LOG"

if [ "$(classification)" != "current-session-bookkeeping" ]; then
  fail "current session changes were not classified as current-session-bookkeeping"
fi

git -C "$REPO" restore -- "$SESSION_LOG"
printf '\nrepo work\n' >> "$REPO/README.md"

if [ "$(classification)" != "repo-work" ]; then
  fail "repo work was not classified as repo-work"
fi

git -C "$REPO" restore -- README.md
printf '\nother evidence\n' >> "$REPO/$OTHER_LOG"

if [ "$(classification)" != "unsupported-dirty" ]; then
  fail "other session log was not classified as unsupported-dirty"
fi

freshness="$(cd "$REPO" && bash scripts/00.chat/main-refresh/check-chat-is-current-with-main/script.sh --require-fresh)"
[[ "$freshness" == *"Freshness: fresh-ahead"* ]] || fail "freshness result changed"
status_output="$(cd "$REPO" && bash scripts/00.chat/main-refresh/show-main-update-status/script.sh)"
[[ "$status_output" == *"no remotes configured"* ]] || fail "normal remote absence changed"

REAL_GIT="$(command -v git)"
export REAL_GIT
mkdir -p "$TMP_ROOT/bin"
cat > "$TMP_ROOT/bin/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
matched=no
case "$FAULT:$1:${2:-}" in
  base:rev-parse:*|branch:branch:--show-current|status:status:*|incoming:diff:*|ref:show-ref:*|remotes:remote:*|branches:branch:--format=*|comparison:rev-list:*) matched=yes ;;
  ahead:rev-list:*) [[ "${3:-}" == main..* ]] && matched=yes ;;
  behind:rev-list:*) [[ "${3:-}" == *..main ]] && matched=yes ;;
esac
if [ "$matched" = yes ]; then
  echo "private-git-canary@example.invalid" >&2
  exit "${FAULT_STATUS:-128}"
fi
if [ "$1" = worktree ] || { [ "$1" = branch ] && [[ "${2:-}" != --* ]]; }; then
  echo mutation-attempted >> "$MUTATION_MARKER"
  exit 99
fi
exec "$REAL_GIT" "$@"
EOF
chmod +x "$TMP_ROOT/bin/git"

assert_failure() {
  local capability="$1" fault="$2" expected="$3" code="${4:-128}" output
  if output="$(cd "$REPO" && PATH="$TMP_ROOT/bin:$PATH" FAULT="$fault" FAULT_STATUS="$code" MUTATION_MARKER="$TMP_ROOT/mutation" \
    bash "scripts/00.chat/main-refresh/$capability/script.sh" 2>&1)"; then
    fail "$capability accepted failed $fault observation"
  fi
  [[ "$output" == *"$expected"* ]] || fail "$capability lost $expected"
  [[ "$output" != *private-git-canary* ]] || fail "$capability leaked native output"
  [[ "$output" != *"classification=clean"* ]] || fail "read failure became clean"
  [ ! -e "$TMP_ROOT/mutation" ] || fail "failed observation permitted mutation"
}

assert_failure classify-refresh-readiness base refresh-base-unresolved 1
assert_failure classify-refresh-readiness base refresh-base-read-failed
assert_failure classify-refresh-readiness branch refresh-branch-read-failed
assert_failure classify-refresh-readiness status refresh-status-read-failed
assert_failure classify-refresh-readiness incoming refresh-incoming-paths-read-failed
assert_failure check-chat-is-current-with-main branch freshness-branch-read-failed
assert_failure check-chat-is-current-with-main ref freshness-base-missing 1
assert_failure check-chat-is-current-with-main ref freshness-base-read-failed
assert_failure check-chat-is-current-with-main ahead freshness-ahead-read-failed
assert_failure check-chat-is-current-with-main behind freshness-behind-read-failed
assert_failure show-main-update-status ref refresh-status-base-missing 1
assert_failure show-main-update-status ref refresh-status-base-read-failed
assert_failure show-main-update-status remotes refresh-status-remotes-read-failed
assert_failure show-main-update-status branches refresh-status-branches-read-failed
assert_failure show-main-update-status comparison refresh-status-comparison-read-failed
# The actual consumer must preserve the producer's reason and stop before mutation.
assert_failure rehearse-refresh-from-main status refresh-status-read-failed
assert_failure rehearse-refresh-from-main incoming refresh-incoming-paths-read-failed

echo "main refresh dirty classifier smoke test passed."
