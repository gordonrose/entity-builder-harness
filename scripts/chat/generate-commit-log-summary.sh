#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for generating chat commit log summaries.
#   portability: llm-workbench-required
#   used_by:
#     - scripts/shared/chat/audit-chat-layer-migration.sh
#     - scripts/shared/chat/smoke-test-chat-script-aliases.sh
#   effects: read-only

exec bash scripts/shared/chat/generate-commit-log-summary.sh "$@"
