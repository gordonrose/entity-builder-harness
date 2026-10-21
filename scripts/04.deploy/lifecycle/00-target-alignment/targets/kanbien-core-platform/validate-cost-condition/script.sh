#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.validate-cost-condition
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Bind the generic provider-condition validator to the fixed core-platform cost-control evidence before an AWS mutation.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.command.kanbien-core-platform.create-runtime-change-set
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/create-change-set/script.py
#   - id: deploy.command.kanbien-core-platform.execute-runtime-change-set
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/deploy.py

ROOT="$(git rev-parse --show-toplevel)"
exec bash "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.sh" \
  --evidence "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/10-foundation/evidence/target-cost-allocation-tag.yml" \
  --required-status verified \
  --required-status waived-by-approved-exception \
  "$@"
