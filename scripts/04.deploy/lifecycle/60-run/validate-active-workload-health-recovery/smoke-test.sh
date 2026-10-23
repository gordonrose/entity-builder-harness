#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-active-workload-health-recovery.wrapper
#   version: 2
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-23"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Run the scope lifecycle, workload health/recovery, and ownership inventory fixtures.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.validate-active-workload-health-recovery
#     path: scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/script.sh
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/validate-active-workload-health-recovery/smoke-test.py"
