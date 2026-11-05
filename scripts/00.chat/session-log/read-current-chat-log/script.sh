#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.read-current-chat-log
#   version: 1
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Print current chat session metadata from the active chat branch log.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   - id: chat.script.session-log.check-commit-prerequisites.smoke-test
#     path: scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh
#   effects:
#   - read-only

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
      echo "ERROR: unknown argument" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if ! BRANCH="$(git branch --show-current 2>/dev/null)"; then
  echo "ERROR: session-branch-read-failed" >&2
  exit 1
fi

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch"
  exit 1
fi

if ! LOG_FILE="$(chat_log_file_for_session "$SESSION_ID" 2>&1)"; then
  case "$LOG_FILE" in
    'ERROR: session-directory-read-failed'|'ERROR: session-metadata-read-failed'|'ERROR: session-date-invalid'|'ERROR: session-log-ambiguous') printf '%s\n' "$LOG_FILE" >&2 ;;
    *) echo "ERROR: session-log-lookup-failed" >&2 ;;
  esac
  exit 1
fi

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log"
  exit 1
fi

if ! METADATA="$(sed -n '/<!-- agentic-session/,/-->/p' "$LOG_FILE" 2>/dev/null \
  | sed '/<!-- agentic-session/d;/-->/d')"; then
  echo "ERROR: session-metadata-read-failed" >&2
  exit 1
fi
if [[ -z "$METADATA" ]]; then
  echo "ERROR: session-metadata-absent" >&2
  exit 1
fi

LATEST_COMMIT_SHA="$(printf '%s\n' "$METADATA" | sed -n 's/^latest_commit_sha: //p' | head -n 1)"

if [ -n "${LATEST_COMMIT_SHA// }" ] && [ "$ALLOW_RECORDED_SESSION" != "yes" ]; then
  echo "ERROR: recorded-session-approval-required"
  echo "Required action: Ask the user to approve continuing this existing chat/worktree, or start a new chat."
  exit 3
fi

printf '%s\n' "$METADATA"
