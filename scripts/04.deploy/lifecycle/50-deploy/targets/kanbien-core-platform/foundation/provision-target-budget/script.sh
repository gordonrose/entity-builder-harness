#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.provision-target-budget.wrapper
#   version: 1
#   status: active
#   created_on: "2026-10-22"
#   updated_on: "2026-10-22"
#   layer: 04.deploy
#   domain: deployment.foundation-cost-control
#   disciplines: [security, sre]
#   kind: script
#   purpose: Run the fixed target-budget provisioning control for kanbien-core-platform.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: aws.workflow.kanbien-core-platform.provision-target-budget
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/10-foundation/provision-target-budget.md
#   effects: [aws-mutation]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/foundation/provision-target-budget/script.py" "$@"
