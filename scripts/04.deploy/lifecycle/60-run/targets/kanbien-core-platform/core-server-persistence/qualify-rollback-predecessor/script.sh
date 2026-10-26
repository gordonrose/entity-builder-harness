#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.qualify-persistence-rollback-predecessor
#   version: 1
#   status: active
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Create a contract-bound candidate compatibility record for a previously qualified rollback image.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.workflow.govern-scope-lifecycle
#     path: .agentic/04.deploy/60-run/workflows/govern-scope-lifecycle.md
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   effects: [writes-files]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/qualify-rollback-predecessor/script.py" "$@"
