#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat new-session command.
#   domain: startup
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/00.chat/command/new/script.sh
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/00.chat/command/new/script.sh "$@"
