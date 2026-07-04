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
TMP_CFO_FIXTURE_ROOT="$(mktemp -d)"

cleanup() {
  rm -f "$TMP_CFO_OUTPUT"
  rm -rf "$TMP_CFO_FIXTURE_ROOT"
}
trap cleanup EXIT

write_cfo_fixture() {
  local day="$1"
  local slug="$2"
  local id="$3"
  local task="$4"
  local tokens="$5"
  local cost="$6"
  local workflow="$7"
  local dir="$TMP_CFO_FIXTURE_ROOT/2026/jan/$day/2026-01-$day-00-00-$slug"

  mkdir -p "$dir"
  cat > "$dir/README.md" <<EOF
# Chat Session: fixture $task

<!-- agentic-session
id: $id
task: $task
branch: chat/$slug
worktree: /tmp/$slug
chat_lifecycle_workflow: $workflow
status: complete
raised_at_utc: 2026-01-${day}T00:00:00Z
latest_commit_at_utc: 2026-01-${day}T00:10:00Z
estimated_chat_tokens: $tokens
estimated_chat_cost: USD $cost estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=fixture; model=fixture-model; rate=USD 0.10/1M tokens; pricing_snapshot=2026-01-01T00:00:00Z
estimated_query_count: 10
-->

## Initial Intent

$task
EOF
}

CFO_FIXTURE_ROOT="$SCRIPT_DIR/fixtures/commitLogs"
if [ -z "$(find "$CFO_FIXTURE_ROOT" -name README.md -type f -print -quit 2>/dev/null)" ]; then
  write_cfo_fixture "01" "chat-workflow-startup-a" "fixture-chat-workflow-startup-a" "chat workflow startup" "100" "0.01" ".agentic/00.chat/workflows/chat-start.md"
  write_cfo_fixture "02" "chat-workflow-startup-b" "fixture-chat-workflow-startup-b" "chat workflow startup" "200" "0.02" ".agentic/00.chat/workflows/chat-start.md"
  write_cfo_fixture "03" "chat-workflow-startup-c" "fixture-chat-workflow-startup-c" "chat workflow startup" "300" "0.03" ".agentic/00.chat/workflows/chat-start.md"
  write_cfo_fixture "04" "unrelated-database-migration" "fixture-unrelated-task" "unrelated database migration" "900" "0.09" ".agentic/product/workflows/database-migration.md"
  CFO_FIXTURE_ROOT="$TMP_CFO_FIXTURE_ROOT"
fi

bash "$REPO_ROOT/scripts/01.harness/metrics/compare-task-token-consumption/script.sh" \
  --task-query "chat workflow startup" \
  --current-tokens 180 \
  --current-cost-usd 0.018 \
  --current-query-count 10 \
  --workflow ".agentic/00.chat/workflows/chat-start.md" \
  --changed-path ".agentic/00.chat/workflows/chat-start.md" \
  --pricing-basis "fixture token and cost basis" \
  --commit-log-root "$CFO_FIXTURE_ROOT" \
  --min-score 0.12 > "$TMP_CFO_OUTPUT"

exec node "$SCRIPT_DIR/script.js" --cfo-output "$TMP_CFO_OUTPUT" "$@"
