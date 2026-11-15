#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.runtime-dependency-preparation.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-11-14"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Exercise shared dependency preparation and retain the existing feature resolver regression through the registered Bash interface.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
exec node --test "$ROOT/scripts/04.deploy/lifecycle/40-package/prepare-runtime-dependencies/prepare-test.mjs" "$ROOT/scripts/04.deploy/lifecycle/40-package/build-entity-smoke-image/dependency-test.mjs"
