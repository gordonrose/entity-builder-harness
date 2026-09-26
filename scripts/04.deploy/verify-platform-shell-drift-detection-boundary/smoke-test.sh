#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-drift-detection-boundary.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Compile and run the source-only drift-detection boundary verifier.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.platform-shell-drift-detection-boundary-check
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -c 'from pathlib import Path; compile(Path("scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.py").read_text(encoding="utf-8"), "verify-platform-shell-drift-detection-boundary.py", "exec")'
bash scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.sh
