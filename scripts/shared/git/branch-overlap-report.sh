#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for reporting chat branch changed-path overlaps.
#   domain: local-merge
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

exec bash "$REPO_ROOT/scripts/00.chat/local-merge/report-chat-branch-overlaps/script.sh" "$@"
