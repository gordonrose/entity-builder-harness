#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for reporting active chat workspaces.
#   domain: reporting
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
#     - .agentic/00.chat/workflows/chat-reporting.md
#   effects: read-only

exec bash scripts/00.chat/reporting/report-chat-workspaces/script.sh "$@"
