#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.inspect-runtime-alignment
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Bind the core platform's qualified package and fixed AWS target to bounded read-only alignment inspection.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.prepare-candidate
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate/script.sh
#   effects: [network]
ROOT="$(git rev-parse --show-toplevel)"
receipt=""
operation="update"
while [ "$#" -gt 0 ]; do
  case "$1" in
    --receipt) receipt="${2:-}"; shift 2;;
    --operation) operation="${2:-}"; shift 2;;
    --json) shift;;
    *) printf '%s\n' 'DIAGNOSTIC_CODE=RUNTIME_ALIGNMENT_ARGUMENTS_INVALID' >&2; exit 2;;
  esac
done
[ -n "$receipt" ] || { printf '%s\n' 'DIAGNOSTIC_CODE=RUNTIME_ALIGNMENT_RECEIPT_REQUIRED' >&2; exit 2; }
case "$operation" in update|restore) ;; *) printf '%s\n' 'DIAGNOSTIC_CODE=RUNTIME_ALIGNMENT_OPERATION_INVALID' >&2; exit 2;; esac
receipt_report="$(bash "$ROOT/scripts/04.deploy/lifecycle/40-package/package-custody-receipt/script.sh" --receipt "$receipt" --expected-target kanbien-core-platform --expected-candidate kanbien-core-server-candidate --expected-package-contract kanbien-core-server-image --expected-program kanbien-core-server --json)" || { printf '%s\n' "$receipt_report"; exit 1; }
digest="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["image_digest"])' <<<"$receipt_report")"
evidence="$(mktemp)"; trap 'rm -f "$evidence"' EXIT
adapter_status=0
bash "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.sh" --profile kanbien-dev --region eu-west-1 --account-id 337159794548 --repository kanbien-core-platform/core-server --image-digest "$digest" --foundation-stack kanbien-core-platform-foundation --runtime-stack kanbien-core-platform-bootstrap-runtime --cluster kanbien-core-platform --delivery-role github-kanbien-core-platform-delivery --execution-role kanbien-core-platform-task-execution --operation "$operation" --accepted-release "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/30-release-evidence/accepted-release.yml" --json >"$evidence" || adapter_status=$?
bash "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.sh" --contract "$ROOT/infra/04.deploy/03.product/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/20-alignment/runtime-alignment-contract.yml" --evidence "$evidence" --json || exit 1
exit "$adapter_status"
