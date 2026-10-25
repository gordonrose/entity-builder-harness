#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.command.check-selection
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Plan focused existing checks or execute authorized local checks without performing later-stage operations.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.script.commit-gates
#     path: scripts/repo/commit-gates/script.sh
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/repo/check-selection/script.py" "$@"
