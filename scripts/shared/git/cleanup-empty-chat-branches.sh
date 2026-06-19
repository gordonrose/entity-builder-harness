#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the empty chat branch cleanup capability.
#   domain: git
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/chat/cleanup-empty-chat-branches.sh
#   effects: branches, writes-files, destructive

exec bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh "$@"
