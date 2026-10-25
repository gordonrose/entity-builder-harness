#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.deployment-operation-diagnostics.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Run focused retained deployment-operation diagnostic regressions.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
ROOT="$(git rev-parse --show-toplevel)"
exec python3 -B "$ROOT/scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.py"
