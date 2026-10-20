#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.assess-platform-shell-artifact-drift.wrapper
#   version: 1
#   status: active
#   created_on: "2026-09-27"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Expose the fixed safe deployment-artifact drift assessment command.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: package.script.platform-shell-artifact-active-drift-assessment
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/assess-platform-shell-artifact-drift/script.py" "$@"
