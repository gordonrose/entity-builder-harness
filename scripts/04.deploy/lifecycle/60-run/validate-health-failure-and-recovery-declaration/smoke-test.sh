#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-health-failure-and-recovery-declaration
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Prove malformed health, safe-failure, recovery, and proof declarations fail without any provider call.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.validate-health-failure-and-recovery-declaration
#     path: scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.sh
ROOT="$(git rev-parse --show-toplevel)"
CHECK="$ROOT/scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.sh"
CONTRACT="$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/00-declaration/declaration-contract.yml"
fixture="$(mktemp)"; trap 'rm -f "$fixture"' EXIT
expect() {
  local code="$1"
  local result
  if result="$("$CHECK" --scope-contract "$fixture" --json 2>&1)"; then
    echo "ERROR: expected declaration validation failure" >&2; exit 1
  fi
  [[ "$result" == *"$code"* ]] || { echo "ERROR: expected $code, got $result" >&2; exit 1; }
}
"$CHECK" --scope-contract "$CONTRACT" --json | grep -q '"verdict": "passed"'
cp "$CONTRACT" "$fixture"
sed -i 's|path: /readyz|path: /livez|' "$fixture"
expect liveness-and-readiness-not-distinct
cp "$CONTRACT" "$fixture"
sed -i '/      owner: platform-runtime/d' "$fixture"
expect proof-live-recovery-owner-missing
cp "$CONTRACT" "$fixture"
sed -i 's/replay-uncertain-operation/replay-any-operation/' "$fixture"
expect automatic-workload-recovery-replay-boundary-missing
cp "$CONTRACT" "$fixture"
sed -i 's/required: \[\]/required: [postgresql]/' "$fixture"
expect dependency-failure-missing-for-declared-dependency
echo 'Health, failure, and recovery declaration tests passed.'
