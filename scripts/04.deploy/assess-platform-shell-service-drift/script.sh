#!/usr/bin/env bash
#
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-service-drift.shell
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Run the bounded staging Service drift assessment.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: deploy.script.assess-platform-shell-service-drift.readme
#     path: scripts/04.deploy/assess-platform-shell-service-drift/README.md
#   effects:
#   - network
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 scripts/04.deploy/assess-platform-shell-service-drift/script.py "$@"
