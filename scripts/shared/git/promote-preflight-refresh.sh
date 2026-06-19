#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for applying a rehearsed refresh from main.
#   domain: main-refresh
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#   effects: branches, worktrees, destructive

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

exec bash "$REPO_ROOT/scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh" "$@"
