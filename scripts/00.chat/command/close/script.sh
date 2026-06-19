#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Dispatch the public chat close command to the closeout prompt capability.
#   domain: command
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/command/dispatcher/script.sh
#     - package.json scripts.chat:close
#   effects: read-only

exec bash scripts/00.chat/closeout/build-closeout-prompt/script.sh "$@"
