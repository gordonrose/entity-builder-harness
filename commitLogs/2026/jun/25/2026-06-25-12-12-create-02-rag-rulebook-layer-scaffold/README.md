# Chat Session: 2026-06-25-12-12 create-02-rag-rulebook-layer-scaffold

<!-- agentic-session
id: 2026-06-25-12-12-create-02-rag-rulebook-layer-scaffold
task: create 02 rag rulebook layer scaffold
branch: chat/2026-06-25-12-12-create-02-rag-rulebook-layer-scaffold
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-25-12-12-create-02-rag-rulebook-layer-scaffold-52906228
layer: harness
mode: implementation
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-25T11:12:51Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/25/rollout-2026-06-25T02-03-04-019efc4d-4c05-7003-b932-f9db433f587e.jsonl
latest_commit_at_utc: 2026-06-25T11:35:51Z
latest_commit_sha: b61e584
chat_duration: 1380s (00:00:23:00)
estimated_chat_tokens: 545810 estimated from chat transcript bytes (2183239 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/25/rollout-2026-06-25T02-03-04-019efc4d-4c05-7003-b932-f9db433f587e.jsonl)
estimated_chat_cost: USD 16.37 estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing
-->

## Initial Intent

create 02 rag rulebook layer scaffold

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Add RAG/Rulebook as first-class layer `02.rag-rulebook`.
- Renumber existing product, deploy, education, and shared metadata layers to
  `03.product`, `04.deploy`, `05.education`, and `06.shared`.
- Keep existing prototype rulebook artifacts in place until a separate governed
  corpus migration assigns final domain corpus homes.
- Add design-only RAG/Rulebook standards for the portable service contract and
  modular domain corpus package shape before building runtime code.
- Record the ordered repo plan for context-packet schema, rulebook index schema,
  read-only index generation, chunk generation, validation, and later corpus
  migration.

## Activity Log

### 2026-06-25T11:12:51Z - Session started

Initial intent: create 02 rag rulebook layer scaffold


### 2026-06-25T11:30:22Z - Commit recorded

Commit: `59d18ed`

Message: Add RAG rulebook layer scaffold

Summary: Added first-class 02.rag-rulebook layer scaffold, routing/classifier coverage, metadata layer renumbering, script-surface docs, and ADR 0022.

ADR impact: ADR 0022 records the new RAG/Rulebook layer and renumbered metadata layers.


### 2026-06-25T11:35:51Z - Commit recorded

Commit: `b61e584`

Message: Plan RAG rulebook service shape

Summary: Added design-only RAG/Rulebook standards for the portable service contract, domain corpus package shape, and ordered repo plan.

ADR impact: No new ADR; this elaborates ADR 0022 within the new RAG/Rulebook layer.

## Commits



- Commit: `59d18ed`
  Time UTC: 2026-06-25T11:30:22Z
  Message: Add RAG rulebook layer scaffold
  Summary: Added first-class 02.rag-rulebook layer scaffold, routing/classifier coverage, metadata layer renumbering, script-surface docs, and ADR 0022.
  ADR impact: ADR 0022 records the new RAG/Rulebook layer and renumbered metadata layers.


- Commit: `b61e584`
  Time UTC: 2026-06-25T11:35:51Z
  Message: Plan RAG rulebook service shape
  Summary: Added design-only RAG/Rulebook standards for the portable service contract, domain corpus package shape, and ordered repo plan.
  ADR impact: No new ADR; this elaborates ADR 0022 within the new RAG/Rulebook layer.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0022-add-rag-rulebook-layer.md
Reason: Adding a first-class agentic layer and renumbering later metadata layers is a durable harness architecture decision.

## Session Metrics

Raised at UTC: 2026-06-25T11:12:51Z
Latest commit at UTC: 2026-06-25T11:35:51Z
Latest commit SHA: b61e584
Chat duration: 1380s (00:00:23:00)
Estimated chat tokens: 545810 estimated from chat transcript bytes (2183239 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/25/rollout-2026-06-25T02-03-04-019efc4d-4c05-7003-b932-f9db433f587e.jsonl)
Estimated chat cost: USD 16.37 estimated from estimated_chat_tokens
Estimated chat cost basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing

## Notes

- None recorded yet.
