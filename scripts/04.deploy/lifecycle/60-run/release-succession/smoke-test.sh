#!/usr/bin/env bash
set -euo pipefail
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.test.release-succession.wrapper
#   version: 2
#   status: active
#   created_on: "2026-11-08"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [security, sre]
#   kind: script
#   purpose: Run disposable immutable-custody and recovery-policy regressions without provider access.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [writes-files]
#   used_by:
#   - id: deploy.command.release-succession
#     path: scripts/04.deploy/lifecycle/60-run/release-succession/script.sh
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
if [[ "${1:-}" == "--ordinary-update" && "$#" == 1 ]]; then
  exec python3 -B scripts/04.deploy/lifecycle/60-run/release-succession/ordinary-update-test.py
fi
if [[ "$#" != 0 ]]; then
  printf '%s\n' 'release-succession-test-arguments-invalid' >&2
  exit 2
fi
exec python3 -B scripts/04.deploy/lifecycle/60-run/release-succession/smoke-test.py

