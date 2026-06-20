# Chat Session: 2026-06-20-09-25 add-reusable-harness-artifact-path-migration-capability-and-

<!-- agentic-session
id: 2026-06-20-09-25-add-reusable-harness-artifact-path-migration-capability-and-
task: add reusable harness artifact path migration capability and use it for 01.harness planning
branch: chat/2026-06-20-09-25-add-reusable-harness-artifact-path-migration-capability-and-
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-20-09-25-add-reusable-harness-artifact-path-migration-capability-and--1918933302
layer: harness
mode: planning
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-20T08:25:39Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-18-32-019ee41c-2bad-73d0-a908-ad000745a61e.jsonl
latest_commit_at_utc: 2026-06-20T08:56:16Z
latest_commit_sha: 5dee35a
chat_duration: 1837s (00:00:30:37)
estimated_chat_tokens: 433082 estimated from chat transcript bytes (1732327 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-18-32-019ee41c-2bad-73d0-a908-ad000745a61e.jsonl)
estimated_chat_cost: USD 12.99 estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing
-->

## Initial Intent

add reusable harness artifact path migration capability and use it for 01.harness planning

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



- Decision: Add reusable artifact path migration capability
  Rationale: Created a harness workflow, standard, planner, checker, and smoke test so future move/rename/remove work starts with active-reference planning instead of ad hoc search.


- Decision: Rename harness namespaces with compatibility symlinks
  Rationale: Canonical routes are now .agentic/01.harness and scripts/01.harness; .agentic/harness and scripts/shared/harness remain as compatibility symlinks for a later safe cleanup after routes are proven.

## Activity Log

### 2026-06-20T08:25:39Z - Session started

Initial intent: add reusable harness artifact path migration capability and use it for 01.harness planning


### 2026-06-20T08:36:22Z - Decision

Decision: Use migration planner for 01.harness rename

Rationale: Planner found active references for both .agentic/harness -> .agentic/01.harness and scripts/shared/harness -> scripts/01.harness; checker blocks the rename unless active references are updated or an explicit compatibility alias/wrapper/pointer is approved.


### 2026-06-20T08:36:22Z - ADR disposition

ADR needed: yes

ADR path: docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md

Reason: Adding reusable path-migration governance and planning a durable .agentic/scripts namespace rename changes harness process and compatibility policy.


### 2026-06-20T08:50:17Z - ADR disposition

ADR needed: yes

ADR path: docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md

Reason: ADR records both reusable artifact-path migration governance and the compatibility-managed .agentic/scripts namespace rename.


### 2026-06-20T08:56:16Z - Commit recorded

Commit: `5dee35a`

Message: Establish canonical 01.harness namespaces

Summary: Renamed harness governance paths to canonical .agentic/01.harness and scripts/01.harness, added artifact path migration workflow/standard/checkers, preserved old paths as compatibility symlinks, and updated active routing, bootstrap, vendor permission, and script references.

ADR impact: ADR added: docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md

## Commits



- Commit: `5dee35a`
  Time UTC: 2026-06-20T08:56:16Z
  Message: Establish canonical 01.harness namespaces
  Summary: Renamed harness governance paths to canonical .agentic/01.harness and scripts/01.harness, added artifact path migration workflow/standard/checkers, preserved old paths as compatibility symlinks, and updated active routing, bootstrap, vendor permission, and script references.
  ADR impact: ADR added: docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0018-govern-artifact-path-migrations.md
Reason: ADR records both reusable artifact-path migration governance and the compatibility-managed .agentic/scripts namespace rename.

## Session Metrics

Raised at UTC: 2026-06-20T08:25:39Z
Latest commit at UTC: 2026-06-20T08:56:16Z
Latest commit SHA: 5dee35a
Chat duration: 1837s (00:00:30:37)
Estimated chat tokens: 433082 estimated from chat transcript bytes (1732327 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-18-32-019ee41c-2bad-73d0-a908-ad000745a61e.jsonl)
Estimated chat cost: USD 12.99 estimated from estimated_chat_tokens
Estimated chat cost basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing

## Notes

- None recorded yet.
