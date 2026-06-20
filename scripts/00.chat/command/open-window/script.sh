#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Dispatch the public chat open-window command to the worktree window capability.
#   domain: command
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/command/dispatcher/script.sh
#     - package.json scripts.chat:open-window
#   effects: opens-gui

exec bash scripts/00.chat/worktree/open-window/script.sh "$@"
