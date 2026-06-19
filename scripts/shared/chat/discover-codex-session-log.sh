#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for Codex session transcript discovery.
#   domain: transcript
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/00.chat/session-log/record-chat-commit/script.sh
#   effects: read-only

exec bash scripts/00.chat/transcript/discover-codex-session-log/script.sh "$@"
