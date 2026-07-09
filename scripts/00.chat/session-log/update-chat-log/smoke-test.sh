#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.session-log.update-chat-log.smoke-test
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Smoke test structured chat log updates.
#   portability:
#     class: reusable
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.update-chat-log.readme
#     path: scripts/00.chat/session-log/update-chat-log/README.md
#   effects:
#   - writes-files
#   - branches
#   - commits
fail() {
  echo "FAIL: $*" >&2
  exit 1
}

SOURCE_ROOT="$(git rev-parse --show-toplevel)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/update-chat-log-smoke.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}

trap cleanup EXIT

REPO="$TMP_ROOT/repo"
SESSION_ID="2026-07-08-22-33-test-context-hygiene"
LOG_DIR="$REPO/commitLogs/2026/jul/08/$SESSION_ID"
LOG_FILE="$LOG_DIR/README.md"

mkdir -p \
  "$REPO/scripts/00.chat/session-log/paths" \
  "$REPO/scripts/00.chat/session-log/update-chat-log" \
  "$LOG_DIR"

git -C "$REPO" init --quiet --initial-branch=main

cp "$SOURCE_ROOT/scripts/00.chat/session-log/paths/lib.sh" "$REPO/scripts/00.chat/session-log/paths/lib.sh"
cp "$SOURCE_ROOT/scripts/00.chat/session-log/update-chat-log/script.sh" "$REPO/scripts/00.chat/session-log/update-chat-log/script.sh"
chmod +x "$REPO/scripts/00.chat/session-log/update-chat-log/script.sh"

cat > "$LOG_FILE" <<EOF
# Chat Session: context hygiene smoke

<!-- agentic-session
id: $SESSION_ID
task: test context hygiene
branch: chat/$SESSION_ID
worktree:
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
-->

## Initial Intent

test context hygiene

## Context Hygiene

- None recorded yet.

## Activity Log

- None recorded yet.
EOF

git -C "$REPO" add .
git -C "$REPO" -c user.name='Smoke Test' -c user.email='smoke@example.invalid' commit --quiet -m 'base'
git -C "$REPO" switch --quiet -c "chat/$SESSION_ID"

bash -c 'cd "$1" && shift && "$@"' sh "$REPO" \
  bash scripts/00.chat/session-log/update-chat-log/script.sh context-hygiene \
    "Noisy tool output was reduced to decisions and test outcomes." \
    "Durable evidence lives in the task commit and session log." \
  >"$TMP_ROOT/update.out"

if grep -q -- '- None recorded yet.' "$LOG_FILE"; then
  fail "context hygiene placeholder remained after update"
fi

grep -q '^- Summary: Noisy tool output was reduced to decisions and test outcomes\.$' "$LOG_FILE" \
  || fail "context hygiene summary was not recorded"

grep -q '^  Durable evidence: Durable evidence lives in the task commit and session log\.$' "$LOG_FILE" \
  || fail "context hygiene durable evidence was not recorded"

grep -q '^### .* - Context hygiene$' "$LOG_FILE" \
  || fail "context hygiene activity entry was not recorded"

echo "update chat log smoke test passed."
