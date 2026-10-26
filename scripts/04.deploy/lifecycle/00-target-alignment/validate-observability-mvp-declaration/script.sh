#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.validate-core-server-persistence-observability-mvp.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Expose the deterministic observability MVP declaration gate.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-observability-collector
#     path: .github/workflows/publish-kanbien-core-platform-observability-collector.yml
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/00-target-alignment/validate-observability-mvp-declaration/script.py" "$@"

