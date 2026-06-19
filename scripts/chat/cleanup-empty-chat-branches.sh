#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for removing empty chat branches through the chat cleanup capability.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/audit-chat-layer-migration.sh
#     - scripts/shared/chat/smoke-test-chat-script-aliases.sh
#   effects: branches, destructive

exec bash scripts/shared/git/cleanup-empty-chat-branches.sh "$@"
