#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for protected commit-log deletion checks.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - .agentic/shared/checklists/before-commit.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

exec bash scripts/00.chat/session-log/check-commitlog-deletions/script.sh "$@"
