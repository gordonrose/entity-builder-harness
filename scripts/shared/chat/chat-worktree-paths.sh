#!/usr/bin/env bash

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility source shim for chat worktree path and metadata helpers.
#   domain: worktree
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/00.chat/worktree/check-write-location/script.sh
#     - scripts/shared/git/verify-local-convergence.sh
#   effects: read-only

# shellcheck source=../../00.chat/worktree/paths/lib.sh
source "scripts/00.chat/worktree/paths/lib.sh"
