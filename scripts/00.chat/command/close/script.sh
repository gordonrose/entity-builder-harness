#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: chat.script.command.close
#   version: 1
#   status: active
#   layer: 00.chat
#   domain: command
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Dispatch the public chat close command to the closeout prompt capability.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#   used_by:
#   - id: chat.script.command.dispatcher
#     path: scripts/00.chat/command/dispatcher/script.sh
#   effects:
#   - read-only

exec bash scripts/00.chat/closeout/build-closeout-prompt/script.sh "$@"
