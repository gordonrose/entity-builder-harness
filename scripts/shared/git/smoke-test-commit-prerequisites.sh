#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for chat commit prerequisite smoke testing.
#   domain: session-log
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#   effects: writes-files, branches, commits

exec bash scripts/00.chat/session-log/check-commit-prerequisites/smoke-test.sh "$@"
