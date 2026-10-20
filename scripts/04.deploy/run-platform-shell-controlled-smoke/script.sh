#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.run-platform-shell-controlled-smoke
#   version: 2
#   status: active
#   created_on: "2026-09-22"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate or perform one bounded, redacted Cognito-protected staging smoke request.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: package.script.platform-shell-controlled-smoke
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/run-platform-shell-controlled-smoke/script.py" "$@"
