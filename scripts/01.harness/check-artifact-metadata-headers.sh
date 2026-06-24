#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Verify metadata headers on newly added or selected harness artifacts through the artifact metadata capability checker.
#   domain: metadata
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/01.harness/standards/artifact-metadata-headers.md
#     - .agentic/01.harness/artifact-metadata/standard.md
#     - .agentic/00.chat/checklists/before-commit.md
#   effects: read-only

repo_root="$(git rev-parse --show-toplevel)"

exec bash "$repo_root/scripts/01.harness/artifact-metadata/check-headers/script.sh" "$@"
