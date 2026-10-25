#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.promote-accepted-scope
#   version: 1
#   status: active
#   created_on: '2026-10-25'
#   updated_on: '2026-10-25'
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Promote a validated accepted scope through one explicit local lifecycle transition.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   - writes-files
#   argument_validation:
#     flag: --validate-arguments
#     effects:
#     - read-only
#   used_by:
#   - id: deploy.workflow.govern-scope-lifecycle
#     path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
exec python3 -B "$(dirname "$0")/script.py" "$@"
