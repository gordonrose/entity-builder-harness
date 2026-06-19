#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat commit log summary smoke test.
#   domain: validation
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#   effects: writes-files

exec bash scripts/00.chat/reporting/generate-commit-log-summary/smoke-test.sh "$@"
