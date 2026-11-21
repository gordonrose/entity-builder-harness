#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.entity-smoke.publication-contract
#   version: 1
#   status: draft
#   created_on: "2026-11-08"
#   updated_on: "2026-11-09"
#   layer: 04.deploy
#   domain: deployment.entity-smoke
#   disciplines: [security, sre]
#   kind: script
#   purpose: Prove isolated publication source and uncertainty controls with local fixtures, never an image push or provider call.
#   portability: {class: internal, targets: []}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.plan.entity-smoke-core-platform
#     path: .agentic/04.deploy/plans/implementation/entity-smoke-core-platform.md
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
bash scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/script.sh --json
python3 -B scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/workflow-test.py
python3 -B scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/publication-test.py
python3 -B scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/entity-smoke-package-custody/pipeline-test.py
