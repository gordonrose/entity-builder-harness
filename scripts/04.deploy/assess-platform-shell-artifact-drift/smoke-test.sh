#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-artifact-drift.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the bounded deployment-artifact drift assessor without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-artifact-active-drift-assessment-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/assess-platform-shell-artifact-drift/script.py").read_text(encoding="utf-8"), "artifact-active-drift.py", "exec")'
result="$(bash scripts/04.deploy/assess-platform-shell-artifact-drift/script.sh --validate --json)"
if [[ "$result" != *'"id": "source-policy"'* || "$result" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: artifact active drift source validation must emit the safe verdict" >&2
  exit 1
fi
if grep -qE 'describe-stack-resource-drifts|create-change-set|execute-change-set|get-secret-value|put-role-policy|expectedvalue|actualvalue' scripts/04.deploy/assess-platform-shell-artifact-drift/script.py; then
  echo "ERROR: artifact active drift assessment must not read resource details, expose values, or mutate configuration" >&2
  exit 1
fi
echo "Artifact active drift assessment local check passed."
