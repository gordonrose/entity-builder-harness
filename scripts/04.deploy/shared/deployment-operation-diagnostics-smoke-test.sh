#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.deployment-operation-diagnostics.wrapper
#   version: 2
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-11-23"
#   layer: 04.deploy
#   domain: deployment.diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Run the separated shared and Core Server Persistence deployment-operation diagnostics regressions.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
ROOT="$(git rev-parse --show-toplevel)"
python3 -B "$ROOT/scripts/04.deploy/shared/deployment-operation-diagnostics-smoke-test.py"
python3 -B "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/deployment-diagnostics/tests/binding-test.py"
exec bash "$ROOT/scripts/04.deploy/shared/safe-command-diagnostics-smoke-test.sh"
