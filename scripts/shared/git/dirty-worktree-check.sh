#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for chat worktree dirty-state checks.
#   domain: worktree
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#     - .agentic/harness/workflows/change-harness.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

exec bash scripts/00.chat/worktree/dirty-worktree-check/script.sh "$@"
