#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.command.open-window
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: command
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Dispatch the public chat open-window command to the worktree window capability.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.command.dispatcher
#     path: scripts/00.chat/command/dispatcher/script.sh
#   effects:
#   - read-only

exec bash scripts/00.chat/worktree/open-window/script.sh "$@"
