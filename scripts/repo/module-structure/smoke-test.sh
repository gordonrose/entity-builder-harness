#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.module-structure.regression
#   version: 2
#   status: active
#   created_on: "2026-11-01"
#   updated_on: "2026-11-15"
#   layer: 03.product
#   domain: architecture
#   disciplines: [architecture, agentic]
#   kind: script
#   purpose: Run bounded structure fixtures and the real source-index regression.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
node --test scripts/repo/workspace-build/dependencies-test.mjs
exec node scripts/repo/module-structure/smoke-test.mjs
