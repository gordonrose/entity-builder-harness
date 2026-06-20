# Chat Session: 2026-06-20-10-09 remove-proven-compatibility-symlinks-for-old-harness-paths

<!-- agentic-session
id: 2026-06-20-10-09-remove-proven-compatibility-symlinks-for-old-harness-paths
task: remove proven compatibility symlinks for old harness paths
branch: chat/2026-06-20-10-09-remove-proven-compatibility-symlinks-for-old-harness-paths
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-20-10-09-remove-proven-compatibility-symlinks-for-old-harness-paths-3026264151
layer: harness
mode: implementation
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-20T09:09:00Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-18-32-019ee41c-2bad-73d0-a908-ad000745a61e.jsonl
latest_commit_at_utc: 2026-06-20T09:11:27Z
latest_commit_sha: 113de5f
chat_duration: 147s (00:00:02:27)
estimated_chat_tokens: 622439 estimated from chat transcript bytes (2489756 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-18-32-019ee41c-2bad-73d0-a908-ad000745a61e.jsonl)
estimated_chat_cost: USD 18.67 estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing
-->

## Initial Intent

remove proven compatibility symlinks for old harness paths

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



- Decision: Remove old harness compatibility symlinks
  Rationale: Active route scans and artifact path migration checks showed no non-history references to .agentic/harness or scripts/shared/harness, so the symlinks were removed after canonical .agentic/01.harness and scripts/01.harness routes were proven.

## Activity Log

### 2026-06-20T09:09:00Z - Session started

Initial intent: remove proven compatibility symlinks for old harness paths


### 2026-06-20T09:10:28Z - Decision

Decision: Remove old harness compatibility symlinks

Rationale: Active route scans and artifact path migration checks showed no non-history references to .agentic/harness or scripts/shared/harness, so the symlinks were removed after canonical .agentic/01.harness and scripts/01.harness routes were proven.


### 2026-06-20T09:10:28Z - ADR disposition

ADR needed: no

Reason: No new ADR; cleanup executes ADR 0018 path migration policy after active references were already moved to canonical 01.harness routes.


### 2026-06-20T09:11:27Z - Commit recorded

Commit: `113de5f`

Message: Remove old harness compatibility symlinks

Summary: Removed the .agentic/harness and scripts/shared/harness symlinks after path migration checks proved active references now use .agentic/01.harness and scripts/01.harness.

ADR impact: No new ADR; executes ADR 0018 cleanup path.

## Commits



- Commit: `113de5f`
  Time UTC: 2026-06-20T09:11:27Z
  Message: Remove old harness compatibility symlinks
  Summary: Removed the .agentic/harness and scripts/shared/harness symlinks after path migration checks proved active references now use .agentic/01.harness and scripts/01.harness.
  ADR impact: No new ADR; executes ADR 0018 cleanup path.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: No new ADR; cleanup executes ADR 0018 path migration policy after active references were already moved to canonical 01.harness routes.

## Session Metrics

Raised at UTC: 2026-06-20T09:09:00Z
Latest commit at UTC: 2026-06-20T09:11:27Z
Latest commit SHA: 113de5f
Chat duration: 147s (00:00:02:27)
Estimated chat tokens: 622439 estimated from chat transcript bytes (2489756 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/20/rollout-2026-06-20T09-18-32-019ee41c-2bad-73d0-a908-ad000745a61e.jsonl)
Estimated chat cost: USD 18.67 estimated from estimated_chat_tokens
Estimated chat cost basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing

## Notes

- None recorded yet.
