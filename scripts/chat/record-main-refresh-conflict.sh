#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for recording main refresh conflicts in chat logs.
#   domain: refresh
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
#     - .agentic/00.chat/workflows/chat-refresh-from-main.md
#   effects: writes-files

exec bash scripts/00.chat/session-log/record-main-refresh-conflict/script.sh "$@"
