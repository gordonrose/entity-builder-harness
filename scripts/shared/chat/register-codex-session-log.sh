#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Record the discovered Codex transcript path in the current chat log.
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#     - scripts/shared/git/record-chat-commit.sh
#   effects: writes-files

# shellcheck source=session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

usage() {
  cat <<'EOF'
Usage:
  register-codex-session-log.sh

Discovers the current chat's Codex JSONL session log and records its path in
the current chat session log metadata.
EOF
}

if [ $# -ne 0 ]; then
  usage >&2
  exit 2
fi

BRANCH="$(git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

CODEX_SESSION_LOG_PATH="$(bash scripts/shared/chat/discover-codex-session-log.sh "$SESSION_ID" "$LOG_FILE")"

if [ ! -f "$CODEX_SESSION_LOG_PATH" ]; then
  echo "ERROR: discovered Codex session log is not a file: $CODEX_SESSION_LOG_PATH" >&2
  exit 1
fi

tmp="$(mktemp)"

awk -v codex_path="$CODEX_SESSION_LOG_PATH" '
  BEGIN {
    in_meta = 0
    wrote_path = 0
  }
  /^<!-- agentic-session/ {
    in_meta = 1
    print
    next
  }
  in_meta && /^codex_session_log_path:/ {
    print "codex_session_log_path: " codex_path
    wrote_path = 1
    next
  }
  in_meta && /^-->/ {
    if (wrote_path == 0) {
      print "codex_session_log_path: " codex_path
      wrote_path = 1
    }
    in_meta = 0
    print
    next
  }
  {
    print
  }
' "$LOG_FILE" > "$tmp"

mv "$tmp" "$LOG_FILE"

echo "Registered Codex session log:"
echo "session_log=$LOG_FILE"
echo "codex_session_log_path=$CODEX_SESSION_LOG_PATH"
