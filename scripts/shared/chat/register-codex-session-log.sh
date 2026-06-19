#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for Codex session transcript registration.
#   domain: transcript
#   portability: llm-workbench-compatibility
#   used_by:
#     - .agentic/00.chat/workflows/chat-start.md
#   effects: writes-files

exec bash scripts/00.chat/transcript/register-codex-session-log/script.sh "$@"
