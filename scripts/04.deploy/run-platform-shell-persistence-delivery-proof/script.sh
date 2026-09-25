#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-persistence-delivery-proof
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: persistence
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Validate or run one fixed Kanbien staging transaction-to-outbox-to-worker delivery proof.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - network
#   used_by:
#   - id: package.script.platform-shell-persistence-delivery-proof
#     path: package.json

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/run-platform-shell-persistence-delivery-proof/script.py" "$@"
