#!/usr/bin/env bash
#
# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.script.run-platform-shell-postgresql-relational-smoke.shell
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: runtime.operations
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Run the bounded PostgreSQL relational delivery and recovery proof.
#   portability:
#     class: internal
#     targets:
#     - kanbien/staging
#   used_by:
#   - id: deploy.script.run-platform-shell-postgresql-relational-smoke.readme
#     path: scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/README.md
#   effects:
#   - network
set -euo pipefail

# This fixed target wrapper intentionally accepts no target, database, task,
# credential, queue, restore identifier, or timing override from a caller.
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 "$ROOT/scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/script.py" "$@"
