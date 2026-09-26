#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-deployment-artifact-store.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: infra.ci-cd
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally smoke test the static Kanbien staging deployment-artifact store policy check.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-deployment-artifact-store
#     path: scripts/04.deploy/verify-platform-shell-deployment-artifact-store/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash scripts/04.deploy/verify-platform-shell-deployment-artifact-store/script.sh
