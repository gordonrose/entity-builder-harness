#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.persistence-accepted-release.validate
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
#   purpose: Validate retained accepted-release evidence without provider queries.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   argument_validation:
#     flag: --validate-arguments
#     effects:
#     - read-only
#   used_by:
#   - id: deploy.workflow.govern-scope-lifecycle
#     path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
exec python3 -B "$(dirname "$0")/script.py" "$@"
