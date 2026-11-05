#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.diagnostics.coverage
#   version: 1
#   status: active
#   created_on: "2026-10-27"
#   updated_on: "2026-10-27"
#   layer: 06.shared
#   domain: diagnostics
#   disciplines: [architecture, security, sre, agentic]
#   kind: script
#   purpose: Enforce independent diagnostic adoption reviews for new and changed executable code.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec python3 -B "$ROOT/scripts/repo/diagnostic-coverage/script.py" "$@"
