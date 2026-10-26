#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.apply-restoration-verifier-surface
#   version: 3
#   status: active
#   created_on: "2026-10-23"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Apply only the reviewed isolated restoration-verifier provider surface, its explicit missing-egress correction, or its exact task-definition-only image correction.
#   portability: { class: internal, targets: [] }
#   effects: [aws-mutation]
#   used_by:
#   - id: aws.workflow.kanbien-core-platform-core-server-persistence-candidate
#     path: .agentic/aws/50-deploy/workflows/targets/kanbien-core-platform/20-scopes/core-server-persistence/create-and-verify-private-postgresql-candidate.md
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/core-server-persistence/apply-restoration-verifier-surface/script.py" "$@"
