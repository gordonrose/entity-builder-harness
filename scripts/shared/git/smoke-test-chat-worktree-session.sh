#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat startup worktree smoke test.
#   domain: startup
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#   effects: writes-files, branches, worktrees, commits

exec bash scripts/00.chat/startup/start-chat-session/smoke-test.sh "$@"
