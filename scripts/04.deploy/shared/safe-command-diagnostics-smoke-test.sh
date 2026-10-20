#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.safe-command-diagnostics
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
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
[[ "$output" == *'token=[REDACTED]'* ]]
[[ "$output" != *'controlled-secret'* ]]
echo 'Safe command diagnostics smoke test passed.'
