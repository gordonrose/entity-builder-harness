#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.command.download-repo
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: command
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Dispatch the public download repo command to the worktree export capability.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.command.dispatcher
#     path: scripts/00.chat/command/dispatcher/script.sh
#   effects:
#   - writes-files

exec bash scripts/00.chat/export/worktree/script.sh "$@"

