#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deployment-reconciliation.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Execute the static deployment reconciliation policy check.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: deploy.script.verify-platform-shell-infrastructure
#     path: scripts/04.deploy/verify-platform-shell-infrastructure/script.sh
#   effects:
#   - read-only

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash scripts/04.deploy/verify-platform-shell-deployment-reconciliation/script.sh
echo "Platform-shell deployment reconciliation policy local check passed."
