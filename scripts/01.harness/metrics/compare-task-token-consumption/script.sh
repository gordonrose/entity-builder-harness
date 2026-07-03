#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.metrics.compare-task-token-consumption
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: governance.agents
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Compare current task token consumption with similar committed chat sessions.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - read-only
#   used_by:
#   - id: harness.agents.cfo-token-efficiency
#     path: .agentic/01.harness/agents/cfo-token-efficiency.md
#   - id: harness.script.metrics.compare-task-token-consumption.readme
#     path: scripts/01.harness/metrics/compare-task-token-consumption/README.md

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

exec node "$SCRIPT_DIR/script.js" "$@"
