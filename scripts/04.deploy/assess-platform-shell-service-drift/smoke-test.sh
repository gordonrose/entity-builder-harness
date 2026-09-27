#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/assess-platform-shell-service-drift/script.py").read_text(encoding="utf-8"), "service-active-drift.py", "exec")'
result="$(bash scripts/04.deploy/assess-platform-shell-service-drift/script.sh --validate --json)"
if [[ "$result" != *'"id": "source-policy"'* || "$result" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: service active drift source validation must emit the safe verdict" >&2
  exit 1
fi
candidate_result="$(bash scripts/04.deploy/assess-platform-shell-service-drift/script.sh --candidate-onboarding --validate --json)"
if [[ "$candidate_result" != *'"schema": "deploy/platform-shell-candidate-preflight-baseline-evidence/v1"'* || "$candidate_result" != *'"verdict": "passed"'* ]]; then
  echo "ERROR: candidate onboarding baseline validation must emit the safe candidate schema" >&2
  exit 1
fi
if grep -qE 'describe-stack-resource-drifts|create-change-set|execute-change-set|get-secret-value|put-role-policy|expectedvalue|actualvalue' scripts/04.deploy/assess-platform-shell-service-drift/script.py; then
  echo "ERROR: service active drift assessment must not read resource details, expose values, or mutate configuration" >&2
  exit 1
fi
echo "Service active drift assessment local check passed."
