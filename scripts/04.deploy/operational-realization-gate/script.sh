#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.operational-realization-gate
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Run the provider-neutral Operational Realization Gate compiler.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: package.script.deployment-realization-validate
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 scripts/04.deploy/operational-realization-gate/script.py "$@"
