#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for creating or verifying chat-owned worktrees.
#   domain: worktree
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/00.chat/command/dispatcher/smoke-test.sh
#     - scripts/00.chat/startup/start-chat-session/smoke-test.sh
#   effects: worktrees

exec bash scripts/00.chat/worktree/ensure-chat-worktree/script.sh "$@"
