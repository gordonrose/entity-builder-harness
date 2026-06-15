#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=../chat/session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

usage() {
  cat <<'EOF'
Usage:
  checkpoint-chat-session-log.sh [message]

Commits only the current chat session log and aggregate commit log summary as
a narrow bookkeeping checkpoint.
Use after record-chat-commit.sh leaves the session log dirty.
EOF
}

if [ $# -gt 1 ]; then
  usage >&2
  exit 2
fi

COMMIT_MESSAGE="${1:-chore(session): checkpoint chat log}"

BRANCH="$(git branch --show-current)"

if ! SESSION_ID="$(chat_session_id_from_branch "$BRANCH")"; then
  echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
  exit 1
fi

LOG_FILE="$(chat_log_file_for_session "$SESSION_ID")"
SUMMARY_FILE="commitLogs/README.md"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

STAGED_FILES="$(git diff --cached --name-only)"

if [ -n "${STAGED_FILES// }" ]; then
  MIXED_STAGED="$(printf '%s\n' "$STAGED_FILES" | awk \
    -v log_file="$LOG_FILE" \
    -v summary_file="$SUMMARY_FILE" \
    '$0 != log_file && $0 != summary_file')"
  if [ -n "${MIXED_STAGED// }" ]; then
    echo "ERROR: cannot checkpoint session bookkeeping with other staged files:" >&2
    printf '%s\n' "$MIXED_STAGED" >&2
    exit 1
  fi
fi

LOG_HAS_CHANGES="no"
SUMMARY_HAS_CHANGES="no"

if ! git ls-files --error-unmatch "$LOG_FILE" >/dev/null 2>&1 ||
   ! git diff --quiet -- "$LOG_FILE" ||
   ! git diff --cached --quiet -- "$LOG_FILE"; then
  LOG_HAS_CHANGES="yes"
fi

if [ -f "$SUMMARY_FILE" ]; then
  if ! git ls-files --error-unmatch "$SUMMARY_FILE" >/dev/null 2>&1 ||
     ! git diff --quiet -- "$SUMMARY_FILE" ||
     ! git diff --cached --quiet -- "$SUMMARY_FILE"; then
    SUMMARY_HAS_CHANGES="yes"
  fi
fi

if [ "$LOG_HAS_CHANGES" = "no" ] && [ "$SUMMARY_HAS_CHANGES" = "no" ]; then
  echo "No session bookkeeping changes to checkpoint."
  exit 0
fi

if [ -f "$SUMMARY_FILE" ]; then
  git add -- "$LOG_FILE" "$SUMMARY_FILE"
  git commit -m "$COMMIT_MESSAGE" -- "$LOG_FILE" "$SUMMARY_FILE"
else
  git add -- "$LOG_FILE"
  git commit -m "$COMMIT_MESSAGE" -- "$LOG_FILE"
fi

echo "Checkpointed chat session bookkeeping:"
echo "Log: $LOG_FILE"
echo "Summary: $SUMMARY_FILE"
