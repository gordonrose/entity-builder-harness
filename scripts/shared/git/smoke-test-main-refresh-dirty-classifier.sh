#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for refresh-readiness classifier smoke coverage.
#   domain: main-refresh
#   portability: llm-workbench-validation
#   used_by:
#     - scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh
#   effects: writes-files, branches, commits

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

exec bash "$REPO_ROOT/scripts/00.chat/main-refresh/classify-refresh-readiness/smoke-test.sh" "$@"
