#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.inventory-deploy-control
#   version: 1
#   status: active
#   created_on: "2026-10-06"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.governance
#   disciplines:
#   - architecture
#   - sre
#   kind: script
#   purpose: Inventory deploy scripts and infrastructure ownership without provider access or mutation.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.deploy-control-inventory
#     path: package.json
#   - id: deploy.script.inventory-deploy-control.readme
#     path: scripts/04.deploy/inventory-deploy-control/README.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/inventory-deploy-control/script.py" "$@"
