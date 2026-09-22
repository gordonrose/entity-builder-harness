#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-controlled-smoke.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally validate the bounded controlled-smoke command without contacting AWS or the public target.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-controlled-smoke-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/run-platform-shell-controlled-smoke/script.py").read_text(encoding="utf-8"), "controlled-smoke-script.py", "exec")'
result="$(bash scripts/04.deploy/run-platform-shell-controlled-smoke/script.sh --validate)"
if [[ "$result" != '{"controlled_smoke":"validated"}' ]]; then
  echo "ERROR: controlled-smoke validation did not emit the safe expected result" >&2
  exit 1
fi

environment_result="$(bash scripts/04.deploy/run-platform-shell-controlled-smoke/script.sh --validate --aws-credential-source environment)"
if [[ "$environment_result" != '{"controlled_smoke":"validated"}' ]]; then
  echo "ERROR: controlled-smoke OIDC environment validation did not emit the safe expected result" >&2
  exit 1
fi

echo "Controlled platform-shell smoke local validation passed."
