#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for recording a task commit in the current chat session log.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - .agentic/shared/checklists/before-commit.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: writes-files

exec bash scripts/00.chat/session-log/record-chat-commit/script.sh "$@"
