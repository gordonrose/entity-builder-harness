#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.accept-release.wrapper
#   version: 2
#   status: active
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [security, sre]
#   kind: script
#   purpose: Expose accepted-release recording only after matching private verification.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.command.kanbien-core-platform.accept-release
#     path: scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/accept-release/script.py
#   effects: [writes-files]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/bootstrap-runtime/accept-release/script.py" "$@"
