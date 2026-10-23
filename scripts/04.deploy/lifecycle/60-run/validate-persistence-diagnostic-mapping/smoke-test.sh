#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-persistence-diagnostic-mapping
#   version: 1
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.persistence-diagnostics
#   disciplines: [security, sre, agentic]
#   kind: script
#   purpose: Exercise positive and negative persistence diagnostic mapping validation fixtures.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.validate-persistence-diagnostic-mapping
#     path: scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/script.sh
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/validate-persistence-diagnostic-mapping/smoke-test.py"
