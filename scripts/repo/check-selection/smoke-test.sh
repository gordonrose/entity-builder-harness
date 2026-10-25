#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: repo.test.check-selection.wrapper
#   version: 1
#   status: active
#   created_on: "2026-10-24"
#   updated_on: "2026-10-25"
#   layer: 06.shared
#   domain: validation
#   disciplines: [agentic, security, sre]
#   kind: script
#   purpose: Exercise focused change selection and declaration coverage with disposable synthetic scopes and no external operations.
#   portability: { class: source-only, targets: [] }
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.command.check-selection
#     path: scripts/repo/check-selection/script.sh
ROOT="$(git rev-parse --show-toplevel)"
exec python3 "$ROOT/scripts/repo/check-selection/smoke-test.py"
