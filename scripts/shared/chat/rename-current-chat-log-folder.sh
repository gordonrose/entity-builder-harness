#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the current chat log folder rename helper.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: writes-files

exec bash scripts/00.chat/session-log/rename-current-chat-log-folder/script.sh "$@"
