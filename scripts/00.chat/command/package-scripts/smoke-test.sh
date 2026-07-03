#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.command.package-scripts.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test package.json chat command scripts against a throwaway repo.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.bootstrap-chat-workbench-repo
#     path: .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   - id: chat.script.bootstrap.audit-chat-bootstrap-file-set
#     path: scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
#   effects:
#   - writes-files

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

CHAT_BRANCH="chat/2026-06-19-test-open-window"
CHAT_SESSION_ID="${CHAT_BRANCH#chat/}"
CHAT_WORKTREE="$TMP_ROOT/chat-worktree"
git -C "$REPO" branch "$CHAT_BRANCH"
git -C "$REPO" worktree add --quiet "$CHAT_WORKTREE" "$CHAT_BRANCH"
mkdir -p "$CHAT_WORKTREE/commitLogs/2026/jun/19/$CHAT_SESSION_ID"
cat > "$CHAT_WORKTREE/commitLogs/2026/jun/19/$CHAT_SESSION_ID/README.md" <<EOF
# Chat Session: test-open-window

<!-- agentic-session
id: $CHAT_SESSION_ID
task: test open window
branch: $CHAT_BRANCH
worktree: $CHAT_WORKTREE
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-06-19T00:00:00Z
-->
EOF

(
  cd "$REPO"
  npm run --silent chat:list > "$TMP_ROOT/list.out"
  npm run --silent chat:commit-log-summary > "$TMP_ROOT/summary.out"
  npm run --silent chat:cleanup-empty-branches -- --dry-run > "$TMP_ROOT/cleanup.out"
  if CHAT_OPEN_WORKTREE_WINDOW=skip npm run --silent chat:open-window -- "$REPO" > "$TMP_ROOT/open-window-root.out" 2>&1; then
    fail "chat:open-window accepted root/main worktree"
  fi
  CHAT_OPEN_WORKTREE_WINDOW=skip npm run --silent chat:open-window -- "$CHAT_WORKTREE" > "$TMP_ROOT/open-window.out"
)

grep -q '^  close$' "$TMP_ROOT/list.out" || fail "chat:list did not list close"
grep -q '^  new$' "$TMP_ROOT/list.out" || fail "chat:list did not list new"
grep -q '^  open-window$' "$TMP_ROOT/list.out" || fail "chat:list did not list open-window"
grep -q '| Total | USD 0.0006 |' "$TMP_ROOT/summary.out" || fail "chat:commit-log-summary did not delegate"
grep -q 'Mode: dry-run' "$TMP_ROOT/cleanup.out" || fail "chat:cleanup-empty-branches did not delegate"
grep -q 'ERROR: refusing to open non-chat worktree branch: main' "$TMP_ROOT/open-window-root.out" || fail "chat:open-window did not reject root/main"
grep -q "Skipping VS Code window open: $CHAT_WORKTREE" "$TMP_ROOT/open-window.out" || fail "chat:open-window did not delegate"

echo "chat package scripts smoke test passed."
