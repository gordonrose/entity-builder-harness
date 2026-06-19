#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for opening-prompt chat session auto-start.
#   domain: startup
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/00.chat/startup/auto-start-missing-session/script.sh "$@"
