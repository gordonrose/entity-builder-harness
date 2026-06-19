#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Start a new governed chat session through request-initialization.
#   domain: startup
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/commands/README.md
#     - scripts/00.chat/command/dispatcher/script.sh
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/shared/chat/request-initialization/start-chat-session.sh "$@"
