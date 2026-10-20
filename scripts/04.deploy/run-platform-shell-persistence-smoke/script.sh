#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-persistence-smoke
#   version: 1
#   status: active
#   created_on: "2026-09-24"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate or perform the one controlled no-body Kanbien staging persistence acceptance request.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: package.script.platform-shell-persistence-smoke
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/run-platform-shell-persistence-smoke/script.py" "$@"
