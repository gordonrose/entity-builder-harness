#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-worker-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate the guarded staging worker-consumer proof source without contacting AWS.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-worker-smoke-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-worker-smoke/script.py").read_text(encoding="utf-8"), "worker-smoke.py", "exec")'
result="$(npm run platform:shell:worker-smoke -- --validate)"
if [[ "$result" != *'"worker_smoke":"validated"'* ]] || [[ "$result" != *'"maximum_wait_seconds":360'* ]]; then
  echo "ERROR: worker smoke validation must emit only the fixed safe-policy result." >&2
  exit 1
fi

if npm run platform:shell:worker-smoke -- --execute >/dev/null 2>&1; then
  echo "ERROR: worker smoke must require an explicit live-operation guard." >&2
  exit 1
fi

echo "Platform-shell worker smoke local validation passed."
