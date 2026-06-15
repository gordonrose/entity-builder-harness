#!/usr/bin/env bash
set -euo pipefail

BRANCH="$(git branch --show-current)"

if [[ ! "$BRANCH" =~ ^chat/[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}-.+ ]]; then
  echo "ERROR: Not on a chat session branch."
  echo "Current branch: $BRANCH"
  echo "Run VS Code task: Start Chat Session"
  exit 1
fi

SESSION="${BRANCH#chat/}"
LOG_FILE="commitLogs/${SESSION}/README.md"

if [ ! -f "$LOG_FILE" ]; then
  echo "ERROR: Missing chat session log."
  echo "Expected: $LOG_FILE"
  echo "Run VS Code task: Start Chat Session"
  exit 1
fi

echo "Chat session OK"
echo "Branch: $BRANCH"
echo "Log: $LOG_FILE"