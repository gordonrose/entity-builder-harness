# Chat Session: 2026-06-19-16-52 upstream-repo-bootstrap-standard

<!-- agentic-session
id: 2026-06-19-16-52-add-shared-upstream-repo-bootstrap-standard-and-chat-workben
task: add shared upstream repo bootstrap standard and chat workbench bootstrap workflow
branch: chat/2026-06-19-16-52-add-shared-upstream-repo-bootstrap-standard-and-chat-workben
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-19-16-52-add-shared-upstream-repo-bootstrap-standard-and-chat-workben-2135145589
layer: harness
mode: implementation
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-19T15:52:28Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T15-57-23-019ee062-f943-71b2-a975-e5a9172decbe.jsonl
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

add shared upstream repo bootstrap standard and chat workbench bootstrap workflow

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.
- Added a shared upstream repo bootstrap standard and chat-specific workbench
  bootstrap workflow.
- Added ADR 0015 for the shared-standard/layer-workflow split.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Decision: Put reusable upstream repo bootstrap rules in a shared standard.
  Rationale: Future frontend, CRUD factory, AWS CI/CD, and chat workbench repos
  should share source/upstream ownership, exclusion, and approval boundaries.
- Decision: Put the first concrete bootstrap workflow in the chat layer.
  Rationale: `llm-workbench` is a chat workbench repo, so the chat layer owns
  its portable file set while consulting the shared standard.

## Activity Log

### 2026-06-19T15:52:28Z - Session started

Initial intent: add shared upstream repo bootstrap standard and chat workbench bootstrap workflow

### 2026-06-19T16:01:00Z - Bootstrap standard and chat workflow added

Added `.agentic/shared/standards/upstream-repo-bootstrap.md` for cross-layer
bootstrap boundaries, `.agentic/00.chat/workflows/bootstrap-chat-workbench-repo.md`
for the first `llm-workbench` bootstrap path, and ADR 0015 for the durable
architecture decision.

Verification:

- `bash scripts/shared/chat/request-initialization/check-classify-task-fixtures.sh`
- `bash scripts/shared/chat/audit-chat-layer-migration.sh`

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0015-use-shared-upstream-repo-bootstrap-standard.md
Reason: The change defines a durable split between cross-layer upstream repo
bootstrap standards and layer-owned bootstrap workflows.

## Session Metrics

Raised at UTC: 2026-06-19T15:52:28Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
