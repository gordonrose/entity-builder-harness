#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.rehearse-accepted-workload-replacement
#   version: 1
#   status: active
#   created_on: "2026-10-21"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Safely preflight or execute one controlled stop and ECS replacement of the accepted bootstrap workload.
#   portability: { class: internal, targets: [] }
#   effects: [aws-mutation]
#   used_by:
#   - id: aws.workflow.kanbien-core-platform.bootstrap-runtime.rehearse-accepted-workload-replacement
#     path: .agentic/aws/60-run/workflows/targets/kanbien-core-platform/20-scopes/bootstrap-runtime/rehearse-accepted-workload-replacement.md

exec python3 "$(dirname "$0")/script.py" "$@"
