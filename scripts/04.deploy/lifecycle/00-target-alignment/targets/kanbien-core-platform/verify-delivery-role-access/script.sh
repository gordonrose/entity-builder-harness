#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.verify-delivery-role-access
#   version: 2
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Bind the fixed core-platform package destination to the generic AWS ECR read-access adapter.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - network
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-core-server
#     path: .github/workflows/publish-kanbien-core-platform-core-server.yml

[ "$#" -eq 0 ] || { printf '%s\n' 'DIAGNOSTIC_CODE=DELIVERY_ACCESS_ARGUMENTS_INVALID' >&2; exit 2; }
ROOT="$(git rev-parse --show-toplevel)"
exec bash "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/ecr-read-access/script.sh" \
  --repository kanbien-core-platform/core-server
