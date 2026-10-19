#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.runnable-program-contract
#   version: 1
#   status: draft
#   layer: 04.deploy
#   domain: deployment.package-candidates
#   disciplines:
#   - agentic
#   - architecture
#   - security
#   - sre
#   kind: script
#   purpose: Validate a provider-neutral runnable-program and package-candidate contract without building or publishing a package.
#   portability:
#     class: reusable
#     targets:
#     - entity-builder
#   effects:
#   - read-only
#   used_by:
#   - id: deploy.workflow.runnable-program-candidates
#     path: .agentic/04.deploy/workflows/runnable-program-candidates.md

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
exec python3 scripts/04.deploy/lifecycle/20-build/runnable-program-contract/script.py "$@"
