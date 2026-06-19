#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for recording main refresh conflicts in chat logs.
#   domain: refresh
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/audit-chat-layer-migration.sh
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#   effects: writes-files

exec bash scripts/shared/chat/record-main-refresh-conflict.sh "$@"
