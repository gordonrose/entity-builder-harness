#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.module-structure.command
#   version: 1
#   status: active
#   created_on: "2026-11-01"
#   updated_on: "2026-11-01"
#   layer: 03.product
#   domain: architecture
#   disciplines: [architecture, agentic]
#   kind: script
#   purpose: Enforce public-index structure without executing product code.
#   portability: {class: source-only, targets: []}
#   effects: [read-only]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec node scripts/repo/module-structure/check.mjs "$@"
