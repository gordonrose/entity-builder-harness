#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-postgresql-reference.smoke-test
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: persistence.operations
#   disciplines:
#   - security
#   - sre
#   - architecture
#   kind: script
#   purpose: Locally smoke test the static Kanbien staging PostgreSQL relational-reference policy check.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.script.verify-platform-shell-postgresql-reference
#     path: scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash scripts/04.deploy/verify-platform-shell-postgresql-reference/script.sh
