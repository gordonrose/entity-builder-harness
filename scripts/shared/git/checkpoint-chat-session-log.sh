#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for checkpointing chat session-log bookkeeping.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/checklists/before-commit.md
#     - .agentic/shared/checklists/before-commit.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: stages-files, commits

exec bash scripts/00.chat/session-log/checkpoint-chat-session-log/script.sh "$@"
