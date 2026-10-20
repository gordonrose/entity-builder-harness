#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.command.new
#   version: 1
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-10-20"
#   layer: 00.chat
#   domain: command
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Dispatch the public chat new-session command to the startup capability.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.command.dispatcher
#     path: scripts/00.chat/command/dispatcher/script.sh
#   effects:
#   - branches
#   - stages-files
#   - worktrees
#   - writes-files

exec bash scripts/00.chat/startup/start-new-chat/script.sh "$@"
