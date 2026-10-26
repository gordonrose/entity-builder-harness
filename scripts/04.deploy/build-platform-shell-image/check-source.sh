#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.check.platform-shell-package-source
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: deployment.delivery-chain
#   disciplines: [architecture, sre]
#   kind: script
#   purpose: Run the existing product, server and assembled runtime-payload checks before packaging.
#   portability: {class: internal, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: deploy.script.build-platform-shell-image
#     path: scripts/04.deploy/build-platform-shell-image/script.sh
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
npm --ignore-scripts run platform:server:check
npm --ignore-scripts run product:kanbien-platform:check
npm --ignore-scripts run platform:server:image-runtime-check
