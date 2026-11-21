#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.task-execute
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Execute one concretely approved initial preparation task or reconcile its original attempt without replay.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [network, writes-files, aws-mutation]
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
ROOT="$(git rev-parse --show-toplevel)"
exec python3 -B "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/task-route.py" --execute "$@"
