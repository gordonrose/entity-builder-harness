#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-metric-coverage.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally validate the bounded metric-coverage command without contacting AWS, SNS, or the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-metric-coverage-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-metric-coverage/script.py").read_text(encoding="utf-8"), "metric-coverage-script.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-metric-coverage/script.sh --validate)"
if [[ "$result" != '{"platform_shell_metric_coverage":"validated"}' ]]; then
  echo "ERROR: metric-coverage validation did not emit the safe expected result" >&2
  exit 1
fi

environment_result="$(bash scripts/04.deploy/run-platform-shell-metric-coverage/script.sh --validate --aws-credential-source environment)"
if [[ "$environment_result" != '{"platform_shell_metric_coverage":"validated"}' ]]; then
  echo "ERROR: metric-coverage OIDC environment validation did not emit the safe expected result" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 scripts/04.deploy/run-platform-shell-metric-coverage/slo-evaluation-test.py

echo "Platform-shell metric-coverage local validation passed."
