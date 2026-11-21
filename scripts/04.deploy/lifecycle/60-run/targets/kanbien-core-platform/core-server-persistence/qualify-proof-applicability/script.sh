#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.qualify-persistence-proof-applicability.wrapper
#   version: 2
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence
#   disciplines: [security, sre]
#   kind: script
#   purpose: Expose read-only validation of historical applicability records; new releases use shared acceptance policy.
#   portability: { class: internal, targets: [] }
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: deploy.command.kanbien-core-platform.qualify-persistence-proof-applicability
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/qualify-proof-applicability/script.py
#   effects: [read-only]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/core-server-persistence/qualify-proof-applicability/script.py" "$@"
