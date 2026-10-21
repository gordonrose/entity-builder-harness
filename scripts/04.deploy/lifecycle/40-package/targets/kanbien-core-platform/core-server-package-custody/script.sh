#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.kanbien-core-platform.core-server-package-custody
#   version: 2
#   status: active
#   layer: 04.deploy
#   domain: deployment.bootstrap-runtime
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Statically verify the fixed core-server package-publication workflow has no target-mutation authority.
#   portability: { class: internal, targets: [] }
#   effects: [read-only]
#   used_by:
#   - id: deploy.test.kanbien-core-platform.core-server-package-custody
#     path: scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/smoke-test.sh
#   created_on: "2026-10-20"
#   updated_on: "2026-10-21"
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/04.deploy/lifecycle/40-package/targets/kanbien-core-platform/core-server-package-custody/verify-workflow.py" "$@"
