#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.assess-platform-shell-foundation-drift.shell
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   kind: command-wrapper
#   purpose: Run the bounded administrator-only Foundation drift classifier.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 scripts/04.deploy/assess-platform-shell-foundation-drift/script.py "$@"
