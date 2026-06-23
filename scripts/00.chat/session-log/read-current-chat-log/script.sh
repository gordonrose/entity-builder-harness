#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Print current chat session metadata from the active chat branch log.
#   domain: session-log
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#     - scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh
#   effects: read-only

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

ALLOW_RECORDED_SESSION="no"

usage() {
  cat <<'EOF'
Usage:
  read-current-chat-log/script.sh [--allow-recorded-session]

Prints current chat session metadata.

By default, refuses to reuse a chat session that already has recorded commits.
Use --allow-recorded-session only after the user explicitly approves continuing
the existing chat session and worktree.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --allow-recorded-session)
      ALLOW_RECORDED_SESSION="yes"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

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

METADATA="$(sed -n '/<!-- agentic-session/,/-->/p' "$LOG_FILE" \
  | sed '/<!-- agentic-session/d;/-->/d')"

LATEST_COMMIT_SHA="$(printf '%s\n' "$METADATA" | sed -n 's/^latest_commit_sha: //p' | head -n 1)"

if [ -n "${LATEST_COMMIT_SHA// }" ] && [ "$ALLOW_RECORDED_SESSION" != "yes" ]; then
  echo "ERROR: recorded-session-approval-required"
  echo "Session: $SESSION_ID"
  echo "Branch: $BRANCH"
  echo "Log: $LOG_FILE"
  echo "Latest commit: $LATEST_COMMIT_SHA"
  echo "Required action: Ask the user to approve continuing this existing chat/worktree, or start a new chat."
  exit 3
fi

printf '%s\n' "$METADATA"
