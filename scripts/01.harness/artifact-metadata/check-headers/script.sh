#!/usr/bin/env bash
set -euo pipefail

# agentic-script:
#   owner: harness
#   purpose: Provide the capability-scoped entrypoint for artifact metadata header checks during migration.
#   domain: metadata
#   portability: llm-workbench-required
#   used_by:
#     - .agentic/01.harness/artifact-metadata/README.md
#     - .agentic/01.harness/artifact-metadata/standard.md
#   effects: read-only

repo_root="$(git rev-parse --show-toplevel)"

exec bash "$repo_root/scripts/01.harness/check-artifact-metadata-headers.sh" "$@"
