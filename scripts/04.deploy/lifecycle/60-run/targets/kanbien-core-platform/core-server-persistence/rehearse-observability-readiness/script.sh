#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-observability-readiness.wrapper
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Invoke the bounded PostgreSQL readiness observability rehearsal controller.
#   portability: { class: internal, targets: [] }
#   argument_validation:
#     flag: --validate-arguments
#     effects: [read-only]
#   used_by:
#   - id: infra.04-deploy.03-product.targets.kanbien-core-platform.scope.core-server-persistence.acceptance-route
#     path: infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/core-server-persistence/00-declaration/acceptance-route-contract.yml
#   effects: [network, writes-files]
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/rehearse-observability-readiness/script.py" "$@"
