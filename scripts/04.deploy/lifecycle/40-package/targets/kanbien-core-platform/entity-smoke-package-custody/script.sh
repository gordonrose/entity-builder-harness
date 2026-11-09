#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.entity-smoke.package-workflow
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Validate the isolated image publication workflow without accessing a provider or qualifying a package.
#   portability: {class: internal, targets: [kanbien-core-platform]}
#   effects: [read-only]
#   used_by:
#   - id: github.workflow.publish-kanbien-core-platform-entity-smoke
#     path: .github/workflows/publish-kanbien-core-platform-entity-smoke.yml
ROOT="$(git rev-parse --show-toplevel)"
exec python3 -B "$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/verify-workflow.py" "$@"
