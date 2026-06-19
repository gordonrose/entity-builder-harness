#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the empty chat branch cleanup smoke test.
#   domain: validation
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh
#   effects: writes-files, branches, commits, destructive

exec bash scripts/00.chat/git/cleanup-empty-chat-branches/smoke-test.sh "$@"
