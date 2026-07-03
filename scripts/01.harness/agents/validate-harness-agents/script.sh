#!/usr/bin/env bash
set -euo pipefail

# agentic-artifact:
#   schema: agentic-artifact/v2
#   id: harness.script.agents.validate-harness-agents
#   version: 1
#   status: active
#   layer: 01.harness
#   domain: governance.agents
#   disciplines:
#   - agentic
#   kind: script
#   purpose: Validate harness review-agent contracts, use cases, templates, workflows, and CFO fixtures.
#   portability:
#     class: required
#     targets:
#     - llm-workbench
#     - entity-builder
#     - design-system-builder
#   effects:
#   - read-only
#   used_by:
#   - id: harness.standards.agent-contracts
#     path: .agentic/01.harness/standards/agent-contracts.md
#   - id: harness.agents.readme
#     path: .agentic/01.harness/agents/README.md

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel)"
TMP_CFO_OUTPUT="$(mktemp)"

cleanup() {
  rm -f "$TMP_CFO_OUTPUT"
}
trap cleanup EXIT

bash "$REPO_ROOT/scripts/01.harness/metrics/compare-task-token-consumption/script.sh" \
  --task-query "chat workflow startup" \
  --current-tokens 180 \
  --commit-log-root "$SCRIPT_DIR/fixtures/commitLogs" \
  --min-score 0.05 > "$TMP_CFO_OUTPUT"

exec node "$SCRIPT_DIR/script.js" --cfo-output "$TMP_CFO_OUTPUT" "$@"
