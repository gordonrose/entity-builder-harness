#!/usr/bin/env bash
set -euo pipefail

BRANCH="$(git branch --show-current)"

case "$BRANCH" in
  chat/*)
    SESSION_ID="${BRANCH#chat/}"
    ;;
  *)
    echo "ERROR: current branch is not a chat branch: $BRANCH"
    exit 1
    ;;
esac

LOG_FILE="commitLogs/${SESSION_ID}/README.md"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: missing chat log: $LOG_FILE"
  exit 1
fi

sed -n '/<!-- agentic-session/,/-->/p' "$LOG_FILE" \
  | sed '/<!-- agentic-session/d;/-->/d'