#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.validate-health-failure-and-recovery-declaration
#   version: 3
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.runtime-safety
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Prove malformed health, safe-failure, recovery, and proof declarations fail without any provider call.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.command.validate-health-failure-and-recovery-declaration
#     path: scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/script.sh
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/validate-health-failure-and-recovery-declaration/smoke-test.py"
