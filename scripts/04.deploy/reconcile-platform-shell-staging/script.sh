#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.reconcile-platform-shell-staging.wrapper
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
#   purpose: Expose the fail-closed Kanbien staging reconciliation command.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: package.script.platform-shell-deployment-reconciliation
#     path: package.json
#   effects:
#   - network

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/reconcile-platform-shell-staging/script.py" "$@"
