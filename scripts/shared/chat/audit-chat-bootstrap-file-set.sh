#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for the chat bootstrap file-set audit capability.
#   domain: bootstrap
#   portability: llm-workbench-compatibility
#   used_by:
#     - docs/harness/architecture/adrs/0017-organize-scripts-by-owner-domain-and-capability.md
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

exec bash scripts/00.chat/bootstrap/audit-chat-bootstrap-file-set/script.sh "$@"
