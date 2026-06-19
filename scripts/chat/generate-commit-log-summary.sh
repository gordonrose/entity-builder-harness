#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Public alias for generating chat commit log summaries.
#   domain: reporting
#   portability: llm-workbench-required
#   used_by:
#     - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
#     - scripts/shared/chat/smoke-test-chat-script-aliases.sh
#   effects: read-only

exec bash scripts/00.chat/reporting/generate-commit-log-summary/script.sh "$@"
