#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-negative-authz-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally validate the bounded negative-authorization smoke policy without contacting AWS or the public target.
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

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-negative-authz-smoke/script.py").read_text(encoding="utf-8"), "negative-authz-smoke.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-negative-authz-smoke/script.sh --validate)"
if [[ "$result" != '{"negative_authz_smoke":"validated"}' ]]; then
  echo "ERROR: negative authorization smoke validation did not emit the safe expected result" >&2
  exit 1
fi

echo "Negative authorization smoke local validation passed."
