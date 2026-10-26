#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.script.audit-artifact-inventory
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 06.shared
#   domain: validation
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Run the complete artifact metadata inventory and coverage audit outside ordinary commit preparation.
#   portability:
#     class: source-only
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: repo.script.audit-artifact-inventory.readme
#     path: scripts/repo/audit-artifact-inventory/README.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

exec bash scripts/01.harness/artifact-metadata/generate-index/script.sh \
  --all --strict --check-coverage
