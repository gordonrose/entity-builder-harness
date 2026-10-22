#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-private-verifier-fault
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Expose only fixed private-verifier rejection and controller-timeout rehearsal cases.
#   portability: { class: internal, targets: [] }
#   effects: [aws-mutation]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.rehearse-private-verifier-fault
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/rehearse-private-verifier-fault/smoke-test.sh
exec python3 "$(dirname "$0")/script.py" "$@"
