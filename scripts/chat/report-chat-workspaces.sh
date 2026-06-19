#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for reporting active chat workspaces.
#   domain: reporting
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/audit-chat-layer-migration.sh
#     - .agentic/00.chat/workflows/chat-reporting.md
#   effects: read-only

exec bash scripts/shared/chat/report-chat-workspaces.sh "$@"
