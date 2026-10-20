#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-package-custody.validate-delivery-access
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.delivery-access
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Bind the core-platform package-custody declaration to generic validation and the AWS IAM-policy coverage adapter.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-core-server
#     path: .github/workflows/publish-kanbien-core-platform-core-server.yml

if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--json" ]; }; then
  printf '%s\n' 'DIAGNOSTIC_CODE=DELIVERY_ACCESS_ARGUMENTS_INVALID' >&2
  exit 2
fi

ROOT="$(git rev-parse --show-toplevel)"
CONTRACT="infra/04.deploy/03.product/targets/kanbien-core-platform/pipelines/github-actions/core-server-package-custody.delivery-access.yml"
TEMPLATE="infra/04.deploy/03.product/targets/kanbien-core-platform/cloudformation/foundation.yml"
WORKFLOW=".github/workflows/publish-kanbien-core-platform-core-server.yml"
POLICY_SOURCE="${TEMPLATE}#DeliveryRole"
COVERAGE="$(mktemp)"
trap 'rm -f "$COVERAGE"' EXIT

python3 "$ROOT/scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage/script.py" \
  --contract "$ROOT/$CONTRACT" \
  --template "$ROOT/$TEMPLATE" \
  --role-logical-id DeliveryRole \
  --provider-policy-source "$POLICY_SOURCE" \
  --output "$COVERAGE"
bash "$ROOT/scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.sh" \
  --contract "$ROOT/$CONTRACT" \
  --workflow "$ROOT/$WORKFLOW" \
  --provider-policy-coverage "$COVERAGE" "$@"
