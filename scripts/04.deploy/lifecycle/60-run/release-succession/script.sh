#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.release-succession
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Govern immutable accepted-release history and atomic target-scope current-release succession.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.release-succession.implementation
#     path: scripts/04.deploy/lifecycle/60-run/release-succession/script.py
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/60-run/release-succession/script.py" "$@"

