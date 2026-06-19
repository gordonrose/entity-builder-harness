#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat session startup engine.
#   domain: startup
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/00.chat/command/dispatcher/smoke-test.sh
#     - scripts/00.chat/startup/start-chat-session/smoke-test.sh
#   effects: branches, worktrees, writes-files, stages-files

exec bash scripts/00.chat/startup/start-chat-session/script.sh "$@"
