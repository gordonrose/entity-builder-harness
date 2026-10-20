#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.test.kanbien-core-platform.target-controls
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Prove fixed core-platform control commands reject target selection and fail closed without external access.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: aws.plan.kanbien-core-platform.release-rehearsal
#     path: docs/aws/kanbien-core-platform-release-rehearsal-plan.md

ROOT="$(git rev-parse --show-toplevel)"
PREPARE="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/prepare-candidate/script.sh"
DEPLOY="$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/deploy-candidate/script.sh"
VERIFY="$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/verify-candidate/script.sh"
DIGEST="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

expect_blocked() {
  local output
  if output="$("$@" 2>&1)"; then
    echo "ERROR: expected fixed target control to block" >&2
    exit 1
  fi
  [[ "$output" == *'"verdict": "blocked"'* ]] || { echo "ERROR: expected blocked verdict" >&2; exit 1; }
  [[ "$output" == *'"code": "blocked-live-target-not-selected"'* ]] || { echo "ERROR: expected unresolved E0 block" >&2; exit 1; }
  [[ "$output" == *'"external_access_attempted": false'* ]] || { echo "ERROR: external access must remain false" >&2; exit 1; }
}

expect_selector_rejected() {
  local output
  if output="$("$1" --target kanbien/staging 2>&1)"; then
    echo "ERROR: target selector must be rejected" >&2
    exit 1
  fi
  [[ "$output" == *'"code": "target-selector-not-allowed"'* ]] || { echo "ERROR: expected target-selector-not-allowed" >&2; exit 1; }
  [[ "$output" != *'kanbien/staging'* ]] || { echo "ERROR: rejected target value must not be echoed" >&2; exit 1; }
}

for source in \
  "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/control-surface.py" \
  "$PREPARE" "$DEPLOY" "$VERIFY"; do
  if rg -n '^(import|from) (subprocess|socket|urllib|requests)|^\s*(aws|gh|curl|docker)\b' "$source" >/dev/null; then
    echo "ERROR: fixed target control contains an external command or client: $source" >&2
    exit 1
  fi
done

expect_blocked "$PREPARE" --json
expect_blocked "$DEPLOY" --candidate-id kanbien-core-server-candidate --image-digest "$DIGEST" --approved-change-set reviewed-change-set
expect_blocked "$VERIFY" --candidate-id kanbien-core-server-candidate --image-digest "$DIGEST" --receipt-reference safe-receipt-reference
expect_selector_rejected "$PREPARE"
expect_selector_rejected "$DEPLOY"
expect_selector_rejected "$VERIFY"

echo "Fixed core-platform target control tests passed."
