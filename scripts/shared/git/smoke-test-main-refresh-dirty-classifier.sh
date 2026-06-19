#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test dirty-state classification before main refresh.
#   domain: git
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#     - scripts/shared/git/classify-main-refresh-dirty-state.sh
#   effects: writes-files, branches, commits

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
  "$REPO/scripts/shared/chat" \
  "$REPO/scripts/shared/git" \
  "$REPO/$(dirname "$SESSION_LOG")" \
  "$REPO/$(dirname "$OTHER_LOG")"

cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" \
  "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/00.chat/reporting/generate-commit-log-summary/script.sh" \
  "$REPO/scripts/00.chat/reporting/generate-commit-log-summary/script.sh"
cp "$SOURCE_ROOT/scripts/shared/git/classify-main-refresh-dirty-state.sh" \
  "$REPO/scripts/shared/git/classify-main-refresh-dirty-state.sh"

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
    bash scripts/shared/git/classify-main-refresh-dirty-state.sh
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

echo "main refresh dirty classifier smoke test passed."
