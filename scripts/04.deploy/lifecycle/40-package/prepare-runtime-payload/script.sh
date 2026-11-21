#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.prepare-runtime-payload.wrapper
#   version: 2
#   status: draft
#   created_on: "2026-11-14"
#   updated_on: "2026-11-15"
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Run shared payload assembly and connected controlled workload reuse through the registered local fixture command.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel)"
node --test "$ROOT/scripts/repo/workspace-build/declarations-test.mjs" \
  "$ROOT/scripts/repo/workspace-build/compile-test.mjs" \
  "$ROOT/scripts/repo/workspace-build/script-test.mjs" \
  "$ROOT/scripts/repo/workspace-build/project-selection-test.mjs" \
  "$ROOT/scripts/repo/workspace-build/runtime-packages-test.mjs" \
  "$ROOT/scripts/repo/workspace-build/check-inputs-test.mjs"
node --test "$ROOT/scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/assemble-test.mjs"
exec python3 -B "$ROOT/scripts/04.deploy/lifecycle/40-package/prepare-runtime-payload/connected-workload-test.py"
