#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.verify-platform-shell-metric-coverage.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-09-22"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally smoke test the static staging metric-coverage policy check.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-metric-coverage
#     path: scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-metric-coverage/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

bash scripts/04.deploy/legacy/kanbien-staging/verify-platform-shell-metric-coverage/script.sh
echo "Platform-shell metric-coverage policy local check passed."
