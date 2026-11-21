#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.smoke-test-entity-smoke-image
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Qualify the finished feature image against disposable TLS PostgreSQL without publishing or accessing AWS.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files]
#   used_by:
#   - id: infra.04-deploy.entity-smoke.image.contract
#     path: infra/04.deploy/03.product/image/entity-smoke/image-contract.yml
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
# Cleanup is a separate bounded recovery path: it validates an existing owned
# reservation and uses the shared exact-resource cleanup adapter. It cannot
# qualify/build an image, create a fixture or call AWS; do not make orphan
# removal depend on a currently broken declaration or changed source tree.
if [[ $# == 2 && "$1" == --cleanup-reservation ]]; then
  exec node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs "$@"
fi
bash scripts/04.deploy/lifecycle/00-target-alignment/declaration-coverage/script.sh \
  --scope-contract infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/entity-smoke/00-declaration/declaration-contract.yml --json
python3 -B scripts/04.deploy/inventory-deploy-control/script.py --delivery --check
node scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/verify-image.mjs "$@"
entity_smoke_tag="kanbien-entity-smoke:qualification"
if [[ $# == 2 && "$1" == --tag ]]; then entity_smoke_tag="$2"; fi
python3 -B scripts/04.deploy/lifecycle/40-package/smoke-test-entity-smoke-image/capability-negative-test.py --image "$entity_smoke_tag"
