#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.session-log.checkpoint-chat-session-log
#   version: 2
#   status: active
#   created_on: "2026-06-15"
#   updated_on: "2026-11-05"
#   layer: 00.chat
#   domain: session-log
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Commit only the current chat session log as bookkeeping.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.session-log.checkpoint-chat-session-log.readme
#     path: scripts/00.chat/session-log/checkpoint-chat-session-log/README.md
#   effects:
#   - stages-files
#   - commits

# shellcheck source=../paths/lib.sh
source "scripts/00.chat/session-log/paths/lib.sh"

usage() {
  cat <<'EOF'
Usage:
  checkpoint-chat-session-log.sh [--dry-run] [message]

Commits only the current chat session log as a narrow bookkeeping checkpoint.
Use after record-chat-commit.sh leaves the session log dirty.
EOF
}

DRY_RUN="no"

if [ $# -gt 2 ]; then
  usage >&2
  exit 2
fi

if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN="yes"
  shift
fi

if [ $# -gt 1 ]; then
  usage >&2
  exit 2
fi

COMMIT_MESSAGE="${1:-chore(session): checkpoint chat log}"

read_failed() { echo "ERROR: checkpoint-observation-unavailable; stage=$1; effect=none." >&2; exit 2; }
observe() { local stage="$1"; shift; "$@" 2>/dev/null || read_failed "$stage"; }
matches() {
  local stage="$1" status; shift
  if "$@" 2>/dev/null; then return 0; else status=$?; fi
  [ "$status" -eq 1 ] && return 1
  read_failed "$stage"
}
BRANCH="$(observe branch git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch." >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log." >&2
  exit 1
fi

STAGED_FILES="$(observe staged-paths git diff --cached --name-only)"

if [ -n "${STAGED_FILES// }" ]; then
  MIXED_STAGED="$(printf '%s\n' "$STAGED_FILES" | observe staged-filter awk \
    -v log_file="$LOG_FILE" \
    '$0 != log_file')"
  if [ -n "${MIXED_STAGED// }" ]; then
    echo "ERROR: cannot checkpoint session bookkeeping with other staged files." >&2
    exit 1
  fi
fi

MIXED_DIRTY="$(
  {
    observe worktree-paths git diff --name-only
    observe staged-paths git diff --cached --name-only
    observe untracked-paths git ls-files --others --exclude-standard
  } | observe dirty-filter awk \
    -v log_file="$LOG_FILE" \
    '$0 != "" && $0 != log_file' \
    | observe dirty-sort sort -u
)"

if [ -n "${MIXED_DIRTY// }" ]; then
  echo "ERROR: cannot checkpoint session bookkeeping with other dirty files." >&2
  exit 1
fi

LOG_HAS_CHANGES="no"

TRACKED_LOG="$(observe tracked-log git ls-files -- "$LOG_FILE")"
if [ -z "$TRACKED_LOG" ] ||
   ! matches worktree-log-diff git diff --quiet -- "$LOG_FILE" ||
   ! matches staged-log-diff git diff --cached --quiet -- "$LOG_FILE"; then
  LOG_HAS_CHANGES="yes"
fi

if [ "$LOG_HAS_CHANGES" = "no" ]; then
  echo "No session bookkeeping changes to checkpoint."
  exit 0
fi

if [ "$DRY_RUN" = "yes" ]; then
  echo "Would checkpoint chat session bookkeeping:"
  echo "Message: $COMMIT_MESSAGE"
  echo "Log: $LOG_FILE"
  exit 0
fi

apply_command() {
  local stage="$1" status; shift
  if "$@" 2>/dev/null; then return 0; else status=$?; fi
  echo "ERROR: checkpoint-operation-failed; stage=$stage; effect=unknown; inspect before retry." >&2
  exit "$status"
}
apply_command stage-log git add -- "$LOG_FILE"
apply_command commit-log git commit -m "$COMMIT_MESSAGE" -- "$LOG_FILE"

echo "Checkpointed chat session bookkeeping:"
echo "Log: $LOG_FILE"
