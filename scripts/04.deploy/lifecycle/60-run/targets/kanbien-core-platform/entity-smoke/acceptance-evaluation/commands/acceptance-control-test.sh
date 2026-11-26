#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.acceptance-controls.wrapper
#   version: 1
#   status: draft
#   created_on: "2026-11-09"
#   updated_on: "2026-11-26"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Run local restore, final-admission, archive and route protocols without AWS or live acceptance mutation.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
#   - id: deploy.test.entity-smoke.composition.wrapper
#     path: scripts/04.deploy/lifecycle/20-build/entity-smoke-composition/smoke-test.sh
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/recovery-and-replacement/restore/restore-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/tests/acceptance-control-test.py
python3 -B scripts/04.deploy/lifecycle/60-run/targets/kanbien-core-platform/entity-smoke/acceptance-evaluation/tests/acceptance-route-test.py
