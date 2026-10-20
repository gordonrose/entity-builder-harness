#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: chat.script.startup.start-new-chat
#   version: 1
#   status: active
#   created_on: "2026-06-19"
#   updated_on: "2026-10-20"
#   layer: 00.chat
#   domain: startup
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Start a new governed chat session through the startup engine.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.commands.readme
#     path: .agentic/00.chat/commands/README.md
#   - id: chat.script.command.dispatcher
#     path: scripts/00.chat/command/dispatcher/script.sh
#   effects:
#   - branches
#   - worktrees
#   - writes-files
#   - stages-files
exec bash scripts/00.chat/startup/start-chat-session/script.sh "$@"
