#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-health-failure-and-recovery-declaration
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Run the deterministic health, safe-failure, recovery, and proof declaration validator.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.workflow.verify-health-failure-and-recovery
#     path: .agentic/04.deploy/60-run/workflows/verify-health-failure-and-recovery.md
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.py" "$@"
