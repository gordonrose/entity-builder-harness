#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.acceptance-state
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate retained feature candidate and current-reference evidence without provider queries.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.entity-smoke.acceptance-route
#     path: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/acceptance-route-contract.yml
exec python3 -B "$(dirname "$0")/acceptance-state.py" "$@"

