#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.adapter.aws.runtime-alignment.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
#   layer: 04.deploy
#   domain: deployment.target-alignment
#   disciplines: [security, sre]
#   kind: script
#   purpose: Provide a stable shell entrypoint for bounded AWS runtime-alignment evidence.
#   portability: { class: reusable, targets: [entity-builder] }
#   effects: [network]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/provider-adapters/aws/runtime-alignment/script.py" "$@"
