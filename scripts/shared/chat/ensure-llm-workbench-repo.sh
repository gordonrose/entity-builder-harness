#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: 00.chat
#   purpose: Compatibility wrapper for ensuring the canonical local llm-workbench upstream repo exists.
#   domain: upstream
#   portability: source-only
#   used_by:
#     - scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh
#     - scripts/shared/harness/run-governed-script.sh
#   effects: network, writes-files

exec bash scripts/00.chat/upstream/ensure-llm-workbench-repo/script.sh "$@"
