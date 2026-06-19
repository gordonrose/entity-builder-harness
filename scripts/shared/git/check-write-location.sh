#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for chat-owned worktree write-location checks.
#   domain: worktree
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - .agentic/00.chat/workflows/chat-start.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

exec bash scripts/00.chat/worktree/check-write-location/script.sh "$@"
