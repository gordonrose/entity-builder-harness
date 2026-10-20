#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-target-alignment.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Provide a stable command entrypoint for provider-neutral target alignment validation.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [read-only]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-target-alignment/script.py" "$@"
