#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-worker-smoke.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-09-23"
#   updated_on: "2026-10-26"
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
#   - writes-files
#   used_by:
#   - id: package.script.platform-shell-worker-smoke-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-worker-smoke/script.py").read_text(encoding="utf-8"), "worker-smoke.py", "exec")'
result="$(npm run platform:shell:worker-smoke -- --validate)"
if [[ "$result" != *'"worker_smoke":"validated"'* ]] || [[ "$result" != *'"message_count":2'* ]] || [[ "$result" != *'"inter_message_wait_seconds":75'* ]] || [[ "$result" != *'"maximum_wait_seconds":360'* ]] || [[ "$result" != *'"metric_export_settlement_wait_seconds":75'* ]]; then
  echo "ERROR: worker smoke validation must emit only the fixed safe-policy result." >&2
  exit 1
fi

if npm run platform:shell:worker-smoke -- --execute >/dev/null 2>&1; then
  echo "ERROR: worker smoke must require an explicit live-operation guard." >&2
  exit 1
fi

python3 -B scripts/04.deploy/run-platform-shell-worker-smoke/recovery-test.py

echo "Platform-shell worker smoke local validation passed."
