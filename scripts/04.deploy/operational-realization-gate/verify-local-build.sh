#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: deploy.command.verify-local-build
#   version: 1
#   status: active
#   layer: 04.deploy
#   domain: deployment.realization
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Invoke locked local compiler and runtime verification outside the read-only compiler core.
#   portability: {class: internal, targets: []}
#   effects: [writes-files, network]
#   used_by:
#   - id: deploy.script.operational-realization-gate.readme
#     path: scripts/04.deploy/operational-realization-gate/README.md

LOCAL_BUILD_DIRECTORY="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -I -B "$LOCAL_BUILD_DIRECTORY/local_build.py" "$@"
