#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.kanbien-core-platform.core-server-package-custody
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Prove the fixed target workflow is statically safe.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.command.kanbien-core-platform.core-server-package-custody
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/script.sh
#   created_on: "2026-10-20"
#   updated_on: "2026-10-20"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/script.sh --json >/dev/null
echo 'Core-server package-custody workflow tests passed.'
