#!/usr/bin/env bash
# agentic-artifact:
#   schema: agentic-artifact/v3
#   id: harness.test.agents.validate-harness-agents.diagnostics
#   version: 1
#   status: active
#   created_on: "2026-10-31"
#   updated_on: "2026-10-31"
#   layer: 01.harness
#   domain: governance.agents
#   disciplines: [agentic, security]
#   kind: script
#   purpose: Dispatch the complete harness-agent diagnostic fixture through the registered Bash interface.
#   portability: {class: source-only, targets: []}
#   effects: [read-only, writes-files]
#   used_by:
#   - id: repo.check-selection.catalog
#     path: scripts/repo/check-selection/checks.yml
set -euo pipefail
exec node "$(dirname "${BASH_SOURCE[0]}")/diagnostic-test.js" "$@"
