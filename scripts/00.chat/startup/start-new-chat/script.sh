#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Start a new governed chat session through the startup engine.
#   domain: startup
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/commands/README.md
#     - scripts/00.chat/command/dispatcher/script.sh
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/00.chat/startup/start-chat-session/script.sh "$@"
