#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-provider-condition-evidence.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines:
#   - security
#   - sre
#   kind: script
#   purpose: Provide a stable shell entrypoint for provider-condition evidence validation.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.test.validate-provider-condition-evidence
#     path: scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/smoke-test.sh

ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-provider-condition-evidence/script.py" "$@"
