<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.fixtures.agents.cfo-session-unrelated
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: example
purpose: Provide an unrelated fixture chat log for CFO token-comparison validation.
portability:
  class: internal
  targets: []
used_by:
- id: harness.script.agents.validate-harness-agents
  path: scripts/01.harness/agents/validate-harness-agents/script.sh
-->

# Chat Session: fixture unrelated task

<!-- agentic-session
id: fixture-unrelated-task
task: unrelated database migration
branch: chat/fixture-d
worktree: /tmp/fixture-d
chat_lifecycle_workflow: .agentic/product/workflows/database-migration.md
status: complete
raised_at_utc: 2026-01-04T00:00:00Z
latest_commit_at_utc: 2026-01-04T00:10:00Z
estimated_chat_tokens: 900
estimated_chat_cost: USD 0.09 estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=fixture; model=fixture-model; rate=USD 0.10/1M tokens; pricing_snapshot=2026-01-01T00:00:00Z
estimated_query_count: 10
-->

## Initial Intent

unrelated database migration
