#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for auditing chat layer migration file placement.
#   domain: migration
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
#     - .agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md
#   effects: read-only

exec bash scripts/00.chat/migration/audit-chat-layer-migration/script.sh "$@"
