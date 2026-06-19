#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for removing empty chat branches through the chat cleanup capability.
#   domain: git
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh
#     - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
#     - scripts/shared/chat/smoke-test-chat-script-aliases.sh
#   effects: branches, destructive

exec bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh "$@"
