#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-secret-dependency-declaration
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.secret-management
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Validate one scope's portable secret dependency declaration without a provider read.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.workflow.declare-secret-dependency
#     path: .agentic/04.deploy/00-target-alignment/workflows/declare-secret-dependency.md
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-secret-dependency-declaration/script.py" "$@"
