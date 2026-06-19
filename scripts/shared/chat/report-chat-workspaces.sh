#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat workspace reporting capability.
#   domain: reporting
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

exec bash scripts/00.chat/reporting/report-chat-workspaces/script.sh "$@"
