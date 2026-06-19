#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public chat command entrypoint for new, close, and list commands.
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/00.chat/commands/README.md
#     - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/shared/chat/chat-command.sh "$@"
