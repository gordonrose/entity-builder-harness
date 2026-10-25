#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-persistence-observability-collector-package-custody
#   version: 1
#   status: draft
#   created_on: "2026-10-25"
#   updated_on: "2026-10-25"
#   layer: 04.deploy
#   domain: deployment.core-server-persistence.observability
#   disciplines: [security, sre]
#   kind: script
#   purpose: Fail closed unless the manual-only private collector custody workflow pins and qualifies the declared ADOT source.
#   portability: { class: internal, targets: [] }
#   used_by:
#   - id: deploy.pipeline.kanbien-core-platform.observability-collector-package-custody
#     path: .github/workflows/publish-kanbien-core-platform-observability-collector.yml
#   effects: [read-only]
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-persistence-observability-collector-package-custody/verify-workflow.py" "$@"
