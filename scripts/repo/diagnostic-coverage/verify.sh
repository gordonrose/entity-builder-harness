#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.diagnostics.verification
#   version: 3
#   status: active
#   created_on: "2026-10-27"
#   updated_on: "2026-11-09"
#   layer: 06.shared
#   domain: diagnostics
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Verify executable diagnostic contracts, exports, affected runtime boundaries and cross-language readers locally.
#   portability: { class: source-only, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [ "$#" -eq 0 ]; then
  exec bash scripts/repo/check-selection/script.sh --aggregate-members diagnostic-runtime-contracts --execute-local --json
fi
if [ "$#" -ne 2 ]; then
  echo "Usage: verify.sh [--security-adapter cognito|dynamodb-rate-limiter | --unit base|server|product|cloudwatch|ecs-fargate]" >&2
  exit 2
fi
if [ "$1" = "--security-adapter" ]; then
  case "$2" in
    cognito) npm --ignore-scripts run platform:adapter:aws:auth:cognito:check ;;
    dynamodb-rate-limiter) npm --ignore-scripts run platform:adapter:aws:security:dynamodb-rate-limiter:check ;;
    *) echo "DIAGNOSTIC_SECURITY_ADAPTER_SELECTION_INVALID" >&2; exit 2 ;;
  esac
  exit 0
fi
if [ "$1" != "--unit" ]; then
    echo "DIAGNOSTIC_VERIFICATION_ARGUMENT_INVALID" >&2
    exit 2
fi
case "$2" in
  base) exec bash scripts/repo/check-selection/script.sh --aggregate-members diagnostic-base-runtime --execute-local --json ;;
  core) exec npm run core:check ;;
  contracts|config|security|observability|health|persistence|runtime|testing|workers) exec npm run "platform:$2:check" ;;
  smoke-app) exec npm run app:platform-smoke:check ;;
  entity-smoke) exec npm --ignore-scripts run app:entity-smoke:check ;;
  cloudwatch) exec npm --ignore-scripts run platform:adapter:aws:observability:cloudwatch:check ;;
  ecs-fargate) exec npm --ignore-scripts run platform:adapter:aws:runtime:ecs-fargate:check ;;
  dynamodb-persistence) exec npm --ignore-scripts run platform:adapter:aws:persistence:dynamodb:check ;;
  sqs-queue) exec npm --ignore-scripts run platform:adapter:aws:queue:sqs:check ;;
  server) exec npm --ignore-scripts run platform:server:check ;;
  product) exec npm --ignore-scripts run product:kanbien-platform:check ;;
  catalog) ;;
  *) echo "DIAGNOSTIC_VERIFICATION_UNIT_INVALID" >&2; exit 2 ;;
esac
node_modules/.bin/tsc -p scripts/repo/diagnostic-coverage/tsconfig.json
NODE_PATH="$ROOT/node_modules" node scripts/repo/diagnostic-coverage/export-catalogs.mjs --compiled-root .cache/diagnostic-catalog-export --check
python3 -B scripts/repo/diagnostic-coverage/smoke-test.py
