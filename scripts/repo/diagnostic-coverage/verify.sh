#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.diagnostics.verification
#   version: 5
#   status: active
#   created_on: "2026-10-27"
#   updated_on: "2026-11-27"
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
describe_npm=false
if [ "${1:-}" = "--describe-npm" ]; then
  describe_npm=true
  shift
fi
run_npm() {
  if "$describe_npm"; then
    local ignored=null
    if [ "${1:-}" = "--ignore-scripts" ]; then ignored=true; fi
    printf '{"npmScript":"%s","ignoreScripts":%s}\n' "${@: -1}" "$ignored"
    exit 0
  fi
  exec npm "$@"
}
if "$describe_npm"; then
  if [ "$#" -eq 0 ] || { [ "$#" -eq 2 ] && [ "$1" = "--unit" ] && { [ "$2" = "base" ] || [ "$2" = "catalog" ]; }; }; then
    printf '{"npmScript":null,"ignoreScripts":null}\n'
    exit 0
  fi
fi
if [ "$#" -eq 0 ]; then
  exec bash scripts/repo/check-selection/script.sh --aggregate-members diagnostic-runtime-contracts --execute-local --json
fi
if [ "$#" -ne 2 ]; then
  echo "Usage: verify.sh [--security-adapter cognito|dynamodb-rate-limiter | --unit base|server|product|cloudwatch|ecs-fargate]" >&2
  exit 2
fi
if [ "$1" = "--security-adapter" ]; then
  case "$2" in
    cognito) run_npm --ignore-scripts run platform:adapter:aws:auth:cognito:check ;;
    dynamodb-rate-limiter) run_npm --ignore-scripts run platform:adapter:aws:security:dynamodb-rate-limiter:check ;;
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
  core) run_npm run core:check ;;
  contracts|config|security|observability|health|persistence|runtime|testing|workers) run_npm run "platform:$2:check" ;;
  smoke-app) run_npm run app:platform-smoke:check ;;
  entity-smoke) run_npm --ignore-scripts run app:entity-smoke:check ;;
  cloudwatch) run_npm --ignore-scripts run platform:adapter:aws:observability:cloudwatch:check ;;
  ecs-fargate) run_npm --ignore-scripts run platform:adapter:aws:runtime:ecs-fargate:check ;;
  lambda) run_npm --ignore-scripts run platform:adapter:aws:runtime:lambda:check ;;
  dynamodb-persistence) run_npm --ignore-scripts run platform:adapter:aws:persistence:dynamodb:check ;;
  sqs-queue) run_npm --ignore-scripts run platform:adapter:aws:queue:sqs:check ;;
  server) run_npm --ignore-scripts run platform:server:check ;;
  product) run_npm --ignore-scripts run product:kanbien-platform:check ;;
  catalog) ;;
  *) echo "DIAGNOSTIC_VERIFICATION_UNIT_INVALID" >&2; exit 2 ;;
esac
node scripts/repo/workspace-build/script.mjs --project-roots --project scripts/repo/diagnostic-coverage/tsconfig.json --unowned-root-prefix infra/04.deploy/03.product/entrypoints/ --generated-json-assets --payload
NODE_PATH="$ROOT/node_modules" node scripts/repo/diagnostic-coverage/export-catalogs.mjs --compiled-root .cache/diagnostic-catalog-export --check
python3 -B scripts/repo/diagnostic-coverage/smoke-test.py
