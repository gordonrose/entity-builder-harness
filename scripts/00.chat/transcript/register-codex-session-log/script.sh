#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.transcript.register-codex-session-log
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: transcript
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Record the discovered Codex transcript path as neutral transcript metadata.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   - id: chat.script.session-log.record-chat-commit
#     path: scripts/00.chat/session-log/record-chat-commit/script.sh
#   effects:
#   - writes-files

# shellcheck source=../../session-log/paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  register-codex-session-log.sh

Discovers the current chat's Codex JSONL session log and records it as neutral
transcript metadata in the current chat session log.
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

CODEX_SESSION_LOG_PATH="$(bash scripts/00.chat/transcript/discover-codex-session-log/script.sh "$SESSION_ID" "$LOG_FILE")"

if [ ! -f "$CODEX_SESSION_LOG_PATH" ]; then
  echo "ERROR: discovered Codex session log is not a file: $CODEX_SESSION_LOG_PATH" >&2
  exit 1
fi

tmp="$(mktemp)"

awk -v transcript_provider="codex" -v transcript_path="$CODEX_SESSION_LOG_PATH" '
  BEGIN {
    in_meta = 0
    wrote_provider = 0
    wrote_path = 0
  }
  /^<!-- agentic-session/ {
    in_meta = 1
    print
    next
  }
  in_meta && /^transcript_provider:/ {
    print "transcript_provider: " transcript_provider
    wrote_provider = 1
    next
  }
  in_meta && /^transcript_path:/ {
    print "transcript_path: " transcript_path
    wrote_path = 1
    next
  }
  in_meta && /^codex_session_log_path:/ {
    next
  }
  in_meta && /^-->/ {
    if (wrote_provider == 0) {
      print "transcript_provider: " transcript_provider
      wrote_provider = 1
    }
    if (wrote_path == 0) {
      print "transcript_path: " transcript_path
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
echo "transcript_provider=codex"
echo "transcript_path=$CODEX_SESSION_LOG_PATH"
