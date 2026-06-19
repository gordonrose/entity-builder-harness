#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Dispatch the public chat new-session command to the startup capability.
#   domain: command
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/command/dispatcher/script.sh
#     - package.json scripts.chat:new
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/00.chat/startup/start-new-chat/script.sh "$@"
