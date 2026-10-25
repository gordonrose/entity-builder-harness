#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.declaration-coverage
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.declaration-coverage
#   disciplines: [agentic, sre]
#   kind: script
#   purpose: Check scope implementation and proof references without executing operations.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.workflow.declaration-coverage
#     path: .agentic/04.deploy/workflows/declaration-coverage.md
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.py" "$@"
