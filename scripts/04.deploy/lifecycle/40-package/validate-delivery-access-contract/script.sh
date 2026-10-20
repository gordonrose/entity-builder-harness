#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-delivery-access-contract.wrapper
#   version: 2
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.delivery-access
#   disciplines:
#   - security
#   kind: script
#   purpose: Invoke the provider-neutral delivery-access contract validator.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.test.validate-delivery-access-contract
#     path: scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/smoke-test.sh
#   - id: deploy.command.validate-delivery-access-contract
#     path: scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.py

ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.py" "$@"
