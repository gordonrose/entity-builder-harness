# Chat Session: 2026-07-03-06-53 llm-workbench-provider-neutral-install

<!-- agentic-session
id: 2026-07-03-06-53-analyze-the-attached-chatgpt-conversation-and-compare-it-to-
task: Analyze the attached ChatGPT conversation and compare it to the current llm-workbench repo, then plan changes so the chat harness can install into blank or existing repos for any LLM in CLI or code assistant mode, excluding removed chat-layer classification.
branch: chat/2026-07-03-06-53-analyze-the-attached-chatgpt-conversation-and-compare-it-to-
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-07-03-06-53-analyze-the-attached-chatgpt-conversation-and-compare-it-to--811018
chat_lifecycle_workflow: .agentic/00.chat/workflows/chat-start.md
status: ready
raised_at_utc: 2026-07-03T05:53:53Z
codex_session_log_path:
latest_context_packet_id:
latest_context_packet_routing_summary:
latest_context_packet_at_utc:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

Analyze the attached ChatGPT conversation and compare it to the current llm-workbench repo, then plan changes so the chat harness can install into blank or existing repos for any LLM in CLI or code assistant mode, excluding removed chat-layer classification.

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- Public export initially carried stale readiness docs, source-maintenance
  harness scripts, and selected maintainer ADRs; these were removed from the
  generated public repo and guarded by contract and portability checks.

## Decisions Made

- Treat `llm-workbench` as a standalone public-beta chat harness with
  provider-neutral defaults, no durable whole-chat classification, and no
  source-repo RAG/rulebook assumptions in the public install path.
- Keep maintainer ADRs in the source repo only; generated public repos and
  installed target repos must be understandable from current public docs.
- Limit public `scripts/01.harness` to portable validation and governed-runner
  helpers instead of exporting source-maintenance tooling.

## Activity Log

### 2026-07-03T05:53:53Z - Session started

Initial intent: Analyze the attached ChatGPT conversation and compare it to the current llm-workbench repo, then plan changes so the chat harness can install into blank or existing repos for any LLM in CLI or code assistant mode, excluding removed chat-layer classification.

### 2026-07-03T14:36:55Z - Implementation complete

Implemented provider-neutral install/export hardening, public-beta standards and
acceptance checks, assistant adapters, portable transcript/cost metrics,
slim public harness-script export, and public ADR exclusion. Temporary evals
were used for new edge cases and removed after passing.

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: This change codifies current public-beta contract and export policy in
existing standards, checklists, validators, and source-side documentation
instead of introducing a new architecture decision record.

## Session Metrics

Raised at UTC: 2026-07-03T05:53:53Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
