#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat command dispatcher capability.
#   domain: command
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/00.chat/command/dispatcher/script.sh "$@"
