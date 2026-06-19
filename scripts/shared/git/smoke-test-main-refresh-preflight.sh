#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for rehearsed-refresh smoke coverage.
#   domain: main-refresh
#   portability: llm-workbench-validation
#   used_by:
#     - scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh
#   effects: writes-files, branches, worktrees, commits, destructive

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

exec bash "$REPO_ROOT/scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh" "$@"
