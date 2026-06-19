#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for auditing chat layer migration file placement.
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/audit-chat-layer-migration.sh
#     - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   effects: read-only

exec bash scripts/shared/chat/audit-chat-layer-migration.sh "$@"
