#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for local-main merge readiness verification.
#   domain: local-merge
#   portability: llm-workbench-compatibility
#   used_by:
#     - scripts/shared/harness/run-governed-script.sh
#   effects: read-only

REPO_ROOT="$(git rev-parse --show-toplevel)"
REPO_ROOT="$(cd "$REPO_ROOT" && pwd -P)"

exec bash "$REPO_ROOT/scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh" "$@"
