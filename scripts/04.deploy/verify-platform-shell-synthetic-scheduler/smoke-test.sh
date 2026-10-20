#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.script.verify-platform-shell-synthetic-scheduler.smoke-test
#   version: 1
#   status: active
#   created_on: "2026-09-22"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Locally smoke test the static temporary synthetic scheduler policy check.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-synthetic-scheduler
#     path: scripts/04.deploy/verify-platform-shell-synthetic-scheduler/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

bash scripts/04.deploy/verify-platform-shell-synthetic-scheduler/script.sh
echo "Platform-shell synthetic scheduler local check passed."
