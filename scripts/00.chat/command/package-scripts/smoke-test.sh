#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Smoke test package.json chat command scripts against a throwaway repo.
#   domain: validation
#   portability: llm-workbench-validation
#   used_by:
#     - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#     - scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
#   effects: writes-files

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/chat-package-scripts-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/scripts/00.chat/closeout/build-closeout-prompt" \
  "$REPO/scripts/00.chat/command/close" \
  "$REPO/scripts/00.chat/command/dispatcher" \
  "$REPO/scripts/00.chat/command/new" \
  "$REPO/scripts/00.chat/command/open-window" \
  "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches" \
  "$REPO/scripts/00.chat/reporting/generate-commit-log-summary" \
  "$REPO/scripts/00.chat/reporting/report-chat-workspaces" \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/startup/start-new-chat" \
  "$REPO/scripts/00.chat/worktree/open-window" \
  "$REPO/scripts/00.chat/worktree/paths" \
  "$REPO/commitLogs/2026/jun/19/test-chat"

git -C "$REPO" init --quiet --initial-branch=main

cp "$SOURCE_ROOT/package.json" "$REPO/package.json"
cp "$SOURCE_ROOT/scripts/00.chat/command/dispatcher/script.sh" "$REPO/scripts/00.chat/command/dispatcher/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/new/script.sh" "$REPO/scripts/00.chat/command/new/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/close/script.sh" "$REPO/scripts/00.chat/command/close/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/command/open-window/script.sh" "$REPO/scripts/00.chat/command/open-window/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/reporting/generate-commit-log-summary/script.sh" "$REPO/scripts/00.chat/reporting/generate-commit-log-summary/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/reporting/report-chat-workspaces/script.sh" "$REPO/scripts/00.chat/reporting/report-chat-workspaces/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/paths/lib.sh" "$REPO/scripts/00.chat/worktree/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/worktree/open-window/script.sh" "$REPO/scripts/00.chat/worktree/open-window/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/startup/start-new-chat/script.sh" "$REPO/scripts/00.chat/startup/start-new-chat/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/closeout/build-closeout-prompt/script.sh" "$REPO/scripts/00.chat/closeout/build-closeout-prompt/script.sh"
cp "$SOURCE_ROOT/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh" "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"
chmod +x \
  "$REPO/scripts/00.chat/closeout/build-closeout-prompt/script.sh" \
  "$REPO/scripts/00.chat/command/dispatcher/script.sh" \
  "$REPO/scripts/00.chat/command/new/script.sh" \
  "$REPO/scripts/00.chat/command/close/script.sh" \
  "$REPO/scripts/00.chat/command/open-window/script.sh" \
  "$REPO/scripts/00.chat/reporting/generate-commit-log-summary/script.sh" \
  "$REPO/scripts/00.chat/reporting/report-chat-workspaces/script.sh" \
  "$REPO/scripts/00.chat/worktree/open-window/script.sh" \
  "$REPO/scripts/00.chat/startup/start-new-chat/script.sh" \
  "$REPO/scripts/00.chat/git/cleanup-empty-chat-branches/script.sh"

cat > "$REPO/commitLogs/2026/jun/19/test-chat/README.md" <<'EOF'
# Chat Session: test-chat

<!-- agentic-session
id: test-chat
chat_duration: 10s
estimated_chat_tokens: 20 tokens
estimated_chat_cost: USD 0.0006 estimated from estimated_chat_tokens
-->
EOF

git -C "$REPO" add package.json scripts commitLogs
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'fixture'

(
  cd "$REPO"
  npm run --silent chat:list > "$TMP_ROOT/list.out"
  npm run --silent chat:commit-log-summary > "$TMP_ROOT/summary.out"
  npm run --silent chat:cleanup-empty-branches -- --dry-run > "$TMP_ROOT/cleanup.out"
  CHAT_OPEN_WORKTREE_WINDOW=skip npm run --silent chat:open-window -- "$REPO" > "$TMP_ROOT/open-window.out"
)

grep -q '^  close$' "$TMP_ROOT/list.out" || fail "chat:list did not list close"
grep -q '^  new$' "$TMP_ROOT/list.out" || fail "chat:list did not list new"
grep -q '^  open-window$' "$TMP_ROOT/list.out" || fail "chat:list did not list open-window"
grep -q '| Total | USD 0.0006 |' "$TMP_ROOT/summary.out" || fail "chat:commit-log-summary did not delegate"
grep -q 'Mode: dry-run' "$TMP_ROOT/cleanup.out" || fail "chat:cleanup-empty-branches did not delegate"
grep -q "Skipping VS Code window open: $REPO" "$TMP_ROOT/open-window.out" || fail "chat:open-window did not delegate"

echo "chat package scripts smoke test passed."
