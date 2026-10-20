#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.verify-platform-shell-drift-detection-boundary.wrapper
#   version: 1
#   status: active
#   created_on: "2026-09-26"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Run the static Kanbien staging drift-detection boundary verifier.
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
python3 scripts/04.deploy/verify-platform-shell-drift-detection-boundary/script.py
