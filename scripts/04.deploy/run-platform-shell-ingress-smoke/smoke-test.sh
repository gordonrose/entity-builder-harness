#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-ingress-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the bounded staging ingress proof source without contacting AWS or the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-ingress-smoke-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-ingress-smoke/script.py").read_text(encoding="utf-8"), "ingress-smoke.py", "exec")'
result="$(npm run platform:shell:ingress-smoke -- --validate)"
if [[ "$result" != *'"ingress_smoke":"validated"'* ]] || [[ "$result" != *'"host_rule_priority":20'* ]]; then
  echo "ERROR: ingress smoke validation must emit only the safe fixed-policy result." >&2
  exit 1
fi

if npm run platform:shell:ingress-smoke -- --validate --execute >/dev/null 2>&1; then
  echo "ERROR: ingress smoke must require exactly one execution mode." >&2
  exit 1
fi

echo "Platform-shell ingress smoke local validation passed."
