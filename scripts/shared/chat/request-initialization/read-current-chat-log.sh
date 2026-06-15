#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

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
