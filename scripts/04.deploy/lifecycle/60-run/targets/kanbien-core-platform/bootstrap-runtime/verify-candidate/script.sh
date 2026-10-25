#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.verify-candidate
#   version: 4
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines:
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Verify the fixed core-platform immutable release through one private verifier task, or reuse its fresh completed evidence.
#   portability:
#     class: internal
#     targets: []
#   effects:
#   - aws-mutation
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: deploy.test.kanbien-core-platform.target-controls
#     path: scripts/04.deploy/lifecycle/50-deploy/targets/kanbien-core-platform/bootstrap-runtime/smoke-test.sh

exec python3 "$(dirname "$0")/verify.py" "$@"
