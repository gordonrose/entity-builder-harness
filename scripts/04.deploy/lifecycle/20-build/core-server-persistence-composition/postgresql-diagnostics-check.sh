#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.postgresql-connection-diagnostics
#   version: 1
#   status: active
#   created_on: "2026-10-26"
#   updated_on: "2026-10-26"
#   layer: 04.deploy
#   domain: persistence.diagnostics
#   disciplines: [security, sre]
#   kind: script
#   purpose: Qualify the PostgreSQL adapter and real-driver diagnostic fixtures for local selection and package construction.
#   portability: { class: internal, targets: [] }
#   effects: [writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
#   - id: deploy.command.build-core-server-persistence-image
#     path: scripts/04.deploy/lifecycle/40-package/build-core-server-persistence-image/script.sh
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
npm run platform:adapter:aws:persistence:postgresql:check
