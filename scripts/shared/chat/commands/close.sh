#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat closeout prompt command.
#   domain: closeout
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/00.chat/command/close/script.sh
#   effects: read-only

exec bash scripts/00.chat/command/close/script.sh "$@"
