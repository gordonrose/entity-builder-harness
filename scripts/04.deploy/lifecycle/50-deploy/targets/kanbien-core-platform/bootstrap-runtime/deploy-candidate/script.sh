#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.deploy-candidate
#   version: 2
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Execute only the exact reviewed core-platform CloudFormation change set derived from a qualified receipt.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - aws-mutation
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh

exec python3 "$(dirname "$0")/deploy.py" "$@"
