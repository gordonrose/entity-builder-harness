#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-package-custody.validate-delivery-access
#   version: 1
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.delivery-access
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate static AWS delivery-role coverage for the persistence-candidate package route.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-persistence-package-custody
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-package-custody/script.sh
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--json" ]; }; then printf '%s\n' 'DIAGNOSTIC_CODE=DELIVERY_ACCESS_ARGUMENTS_INVALID' >&2; exit 2; fi
ROOT="$(git rev-parse --show-toplevel)"
CONTRACT="infra/04.deploy/03.product/targets/kanbien-core-platform/40-package-custody/github-actions/core-server-persistence-package-custody.delivery-access.yml"
TEMPLATE="infra/04.deploy/03.product/targets/kanbien-core-platform/30-provider-realization/aws/cloudformation/foundation.yml"
WORKFLOW=".github/workflows/publish-kanbien-core-platform-core-server-persistence.yml"
COVERAGE="$(mktemp)"; trap 'rm -f "$COVERAGE"' EXIT
python3 "$ROOT/scripts/04.deploy/lifecycle/40-package/provider-adapters/aws/iam-policy-coverage/script.py" --contract "$ROOT/$CONTRACT" --template "$ROOT/$TEMPLATE" --role-logical-id DeliveryRole --provider-policy-source "${TEMPLATE}#DeliveryRole" --output "$COVERAGE"
bash "$ROOT/scripts/04.deploy/lifecycle/40-package/validate-delivery-access-contract/script.sh" --contract "$ROOT/$CONTRACT" --workflow "$ROOT/$WORKFLOW" --provider-policy-coverage "$COVERAGE" "$@"
