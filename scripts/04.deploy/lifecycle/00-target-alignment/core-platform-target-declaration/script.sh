#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.core-platform-target-declaration
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Validate the planned core-platform target declaration without reading or mutating external state.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.test.core-platform-target-declaration
#     path: scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/core-platform-target-declaration/script.py" "$@"
