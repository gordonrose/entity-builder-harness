#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: deploy.command.ordinary-update
#   version: 1
#   status: draft
#   created_on: "2026-11-19"
#   updated_on: "2026-11-19"
#   layer: 04.deploy
#   domain: deployment.release-lifecycle
#   disciplines: [architecture, security, sre]
#   kind: script
#   purpose: Connect explicitly authorised ordinary update operations through existing declared owners.
#   portability: {class: reusable, targets: [entity-builder]}
#   effects: [network, writes-files, aws-mutation]
#   argument_validation: {flag: --validate-arguments, effects: [read-only]}
#   used_by:
#   - id: deploy.workflow.verify-accept-or-restore-release
#     path: .agentic/04.deploy/60-run/workflows/verify-accept-or-restore-release.md
set -euo pipefail
exec python3 -B "$(dirname "$0")/ordinary-update.py" "$@"
