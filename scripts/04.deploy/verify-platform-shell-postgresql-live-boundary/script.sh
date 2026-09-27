#!/usr/bin/env bash
#
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.verify-platform-shell-postgresql-live-boundary.shell
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Verify the bounded PostgreSQL live boundary.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: aws.runbook.kanbien-staging-postgresql-relational-reference-v1-stage6
#     path: docs/aws/kanbien-staging-postgresql-relational-reference-v1-stage6-runbook.md
#   effects:
#   - network
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 scripts/04.deploy/verify-platform-shell-postgresql-live-boundary/script.py "$@"
