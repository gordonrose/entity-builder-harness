#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-persistence-admission-probe.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify that the write-admission probe stays fixed, no-body, and non-mutating without contacting AWS or the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.py").read_text(encoding="utf-8"), "persistence-admission-probe.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh --validate)"
if [[ "$result" != '{"persistence_admission_probe":"validated"}' ]]; then
  echo "ERROR: persistence admission-probe validation did not emit the safe expected result" >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh --execute >/dev/null 2>&1; then
  echo "ERROR: the admission probe must refuse execution before its service deployment" >&2
  exit 1
fi

if bash scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.sh --validate --execute >/dev/null 2>&1; then
  echo "ERROR: the admission probe must accept exactly one operating mode" >&2
  exit 1
fi

if rg -n 'smoke/work-items"|X-Request-Id|data=.*admission|request_acceptance|atomicWriter|repository' scripts/04.deploy/run-platform-shell-persistence-admission-probe/script.py >/dev/null; then
  echo "ERROR: the admission probe must not contain a write route, request identity, request body, or persistence seam" >&2
  exit 1
fi

echo "Persistence admission-probe local validation passed."
