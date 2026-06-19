#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the current chat log metadata reader.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#   effects: read-only

exec bash scripts/00.chat/session-log/read-current-chat-log/script.sh "$@"
