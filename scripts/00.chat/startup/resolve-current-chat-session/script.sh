#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.startup.resolve-current-chat-session
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: startup
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Resolve startup to current chat metadata or auto-start a missing session.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.workflows.chat-start
#     path: .agentic/00.chat/workflows/chat-start.md
#   effects:
#   - branches
#   - worktrees
#   - writes-files
#   - stages-files

OPENING_PROMPT="${*:-}"

set +e
CURRENT_METADATA="$(bash scripts/00.chat/session-log/read-current-chat-log/script.sh 2>&1)"
READ_STATUS=$?
set -e

if [ "$READ_STATUS" -eq 0 ]; then
  printf '%s\n' "$CURRENT_METADATA"
  exit 0
fi

case "$CURRENT_METADATA" in
  *"ERROR: current branch is not a chat branch:"*|*"ERROR: missing chat log:"*)
    exec bash scripts/00.chat/startup/auto-start-missing-session/script.sh "$OPENING_PROMPT"
    ;;
esac

printf '%s\n' "$CURRENT_METADATA"
exit "$READ_STATUS"
