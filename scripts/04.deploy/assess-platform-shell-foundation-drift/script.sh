#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-foundation-drift.shell
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Run the bounded administrator-only Foundation drift classifier.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: deploy.script.assess-platform-shell-foundation-drift.readme
#     path: scripts/04.deploy/assess-platform-shell-foundation-drift/README.md
#   effects:
#   - network

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 scripts/04.deploy/assess-platform-shell-foundation-drift/script.py "$@"
