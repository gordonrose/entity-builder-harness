#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  checkpoint-chat-session-log.sh [message]

Commits only the current chat session log as a narrow bookkeeping checkpoint.
Use after record-chat-commit.sh leaves the session log dirty.
EOF
}

if [ $# -gt 1 ]; then
  usage >&2
  exit 2
fi

COMMIT_MESSAGE="${1:-chore(session): checkpoint chat log}"

BRANCH="$(git branch --show-current)"

case "$BRANCH" in
  chat/*)
    SESSION_ID="${BRANCH#chat/}"
    ;;
  *)
    echo "ERROR: current branch is not a chat branch: $BRANCH" >&2
    exit 1
    ;;
esac

LOG_FILE="commitLogs/${SESSION_ID}/README.md"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE" >&2
  exit 1
fi

STAGED_FILES="$(git diff --cached --name-only)"

if [ -n "${STAGED_FILES// }" ]; then
  MIXED_STAGED="$(printf '%s\n' "$STAGED_FILES" | awk -v log_file="$LOG_FILE" '$0 != log_file')"
  if [ -n "${MIXED_STAGED// }" ]; then
    echo "ERROR: cannot checkpoint session log with other staged files:" >&2
    printf '%s\n' "$MIXED_STAGED" >&2
    exit 1
  fi
fi

if git diff --quiet -- "$LOG_FILE" &&
   git diff --cached --quiet -- "$LOG_FILE" &&
   git ls-files --error-unmatch "$LOG_FILE" >/dev/null 2>&1; then
  echo "No session log changes to checkpoint: $LOG_FILE"
  exit 0
fi

git add -- "$LOG_FILE"
git commit -m "$COMMIT_MESSAGE" -- "$LOG_FILE"

echo "Checkpointed chat session log: $LOG_FILE"
