#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/chat-script-aliases-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
mkdir -p \
  "$REPO/scripts/chat" \
  "$REPO/scripts/shared/chat/commands" \
  "$REPO/scripts/shared/git" \
  "$REPO/commitLogs/2026/jun/19/test-chat"

git -C "$REPO" init --quiet --initial-branch=main

cp "$SOURCE_ROOT"/scripts/chat/*.sh "$REPO/scripts/chat/"
cp "$SOURCE_ROOT/scripts/shared/chat/chat-command.sh" "$REPO/scripts/shared/chat/chat-command.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/generate-commit-log-summary.sh" "$REPO/scripts/shared/chat/generate-commit-log-summary.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/report-chat-workspaces.sh" "$REPO/scripts/shared/chat/report-chat-workspaces.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/session-log-paths.sh" "$REPO/scripts/shared/chat/session-log-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/chat-worktree-paths.sh" "$REPO/scripts/shared/chat/chat-worktree-paths.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/commands/new.sh" "$REPO/scripts/shared/chat/commands/new.sh"
cp "$SOURCE_ROOT/scripts/shared/chat/commands/close.sh" "$REPO/scripts/shared/chat/commands/close.sh"
cp "$SOURCE_ROOT/scripts/shared/git/cleanup-empty-chat-branches.sh" "$REPO/scripts/shared/git/cleanup-empty-chat-branches.sh"
chmod +x "$REPO"/scripts/chat/*.sh "$REPO"/scripts/shared/chat/*.sh "$REPO"/scripts/shared/chat/commands/*.sh "$REPO"/scripts/shared/git/*.sh

cat > "$REPO/commitLogs/2026/jun/19/test-chat/README.md" <<'EOF'
# Chat Session: test-chat

<!-- agentic-session
id: test-chat
chat_duration: 10s
estimated_chat_tokens: 20 tokens
estimated_chat_cost: USD 0.0006 estimated from estimated_chat_tokens
-->
EOF

git -C "$REPO" add scripts commitLogs
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'fixture'

(
  cd "$REPO"
  bash scripts/chat/chat-command.sh list > "$TMP_ROOT/list.out"
  bash scripts/chat/generate-commit-log-summary.sh > "$TMP_ROOT/summary.out"
  bash scripts/chat/cleanup-empty-chat-branches.sh --dry-run > "$TMP_ROOT/cleanup.out"
)

grep -q '^  close$' "$TMP_ROOT/list.out" || fail "chat-command alias did not list close"
grep -q '^  new$' "$TMP_ROOT/list.out" || fail "chat-command alias did not list new"
grep -q '| Total | USD 0.0006 |' "$TMP_ROOT/summary.out" || fail "summary alias did not delegate"
grep -q 'Mode: dry-run' "$TMP_ROOT/cleanup.out" || fail "cleanup alias did not delegate"

echo "chat script aliases smoke test passed."
