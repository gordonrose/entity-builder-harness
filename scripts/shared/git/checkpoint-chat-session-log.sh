#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Commit only the current chat session log as bookkeeping.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - .agentic/shared/checklists/before-commit.md
#   effects: stages-files, commits

# shellcheck source=../chat/session-log-paths.sh
source "scripts/shared/chat/session-log-paths.sh"

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

STAGED_FILES="$(git diff --cached --name-only)"

if [ -n "${STAGED_FILES// }" ]; then
  MIXED_STAGED="$(printf '%s\n' "$STAGED_FILES" | awk \
    -v log_file="$LOG_FILE" \
    '$0 != log_file')"
  if [ -n "${MIXED_STAGED// }" ]; then
    echo "ERROR: cannot checkpoint session bookkeeping with other staged files:" >&2
    printf '%s\n' "$MIXED_STAGED" >&2
    exit 1
  fi
fi

MIXED_DIRTY="$(
  {
    git diff --name-only
    git diff --cached --name-only
    git ls-files --others --exclude-standard
  } | awk \
    -v log_file="$LOG_FILE" \
    '$0 != "" && $0 != log_file' \
    | sort -u
)"

if [ -n "${MIXED_DIRTY// }" ]; then
  echo "ERROR: cannot checkpoint session bookkeeping with other dirty files:" >&2
  printf '%s\n' "$MIXED_DIRTY" >&2
  exit 1
fi

LOG_HAS_CHANGES="no"

if ! git ls-files --error-unmatch "$LOG_FILE" >/dev/null 2>&1 ||
   ! git diff --quiet -- "$LOG_FILE" ||
   ! git diff --cached --quiet -- "$LOG_FILE"; then
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

git add -- "$LOG_FILE"
git commit -m "$COMMIT_MESSAGE" -- "$LOG_FILE"

echo "Checkpointed chat session bookkeeping:"
echo "Log: $LOG_FILE"
