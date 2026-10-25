#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.safe-command-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Prove the shared diagnostic wrapper preserves a safe failure signal without leaking a controlled secret fixture.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.shared.safe-command-diagnostics
#     path: scripts/04.deploy/shared/safe-command-diagnostics.sh

ROOT="$(git rev-parse --show-toplevel)"
source "$ROOT/scripts/04.deploy/shared/safe-command-diagnostics.sh"
if output="$(safe_command_diagnostic TEST_CHILD_FAILURE 40-package 'controlled child failed' 'inspect fixture' -- bash -c 'printf "token=controlled-secret\\n"; exit 17' 2>&1)"; then
  echo 'ERROR: safe diagnostic wrapper accepted a failed child command.' >&2
  exit 1
else
  status=$?
fi
[[ "$status" -eq 17 ]]
[[ "$output" == *'DIAGNOSTIC_CODE=TEST_CHILD_FAILURE'* ]]
[[ "$output" == *'CHILD_OUTPUT=not-retained-unstructured-output'* ]]
[[ "$output" != *'controlled-secret'* ]]
report="$(mktemp)"
trap 'rm -f "$report"' EXIT
if output="$(safe_command_deployment_diagnostic TEST_CHILD_FAILURE package 'controlled child failed' 'inspect fixture' test-target test-scope test-operation github-actions-artifact:diagnostics-test "$report" -- bash -c 'printf "token=controlled-secret\\n"; exit 17' 2>&1)"; then
  echo 'ERROR: safe deployment diagnostic accepted a failed child command.' >&2
  exit 1
else
  status=$?
fi
[[ "$status" -eq 17 ]]
[[ "$output" == *'DIAGNOSTIC_COLLECTION_STATUS=collected'* ]]
[[ "$output" != *'controlled-secret'* ]]
python3 "$ROOT/scripts/04.deploy/shared/deployment-operation-diagnostics.py" validate --report "$report" >/dev/null
[[ "$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["original_failure"]["exit_status"])' "$report")" == 17 ]]
echo 'Safe command diagnostics smoke test passed.'
