#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Print current chat session metadata from the active chat branch log.
#   domain: session-log
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#     - scripts/shared/git/smoke-test-commit-prerequisites.sh
#   effects: read-only

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

BRANCH="$(git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH"
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE"
  exit 1
fi

sed -n '/<!-- agentic-session/,/-->/p' "$LOG_FILE" \
  | sed '/<!-- agentic-session/d;/-->/d'
