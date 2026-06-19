# Chat Session: 2026-06-19-17-06 bootstrap-initial-git-state

<!-- agentic-session
id: 2026-06-19-17-06-tighten-upstream-workbench-bootstrap-workflow-for-initial-gi
task: tighten upstream workbench bootstrap workflow for initial git setup and commitLogs behavior
branch: chat/2026-06-19-17-06-tighten-upstream-workbench-bootstrap-workflow-for-initial-gi
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-19-17-06-tighten-upstream-workbench-bootstrap-workflow-for-initial-gi-3936968791
layer: harness
mode: implementation
workflow: .agentic/harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-19T16:06:50Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/19/rollout-2026-06-19T15-57-23-019ee062-f943-71b2-a975-e5a9172decbe.jsonl
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

tighten upstream workbench bootstrap workflow for initial git setup and commitLogs behavior

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.
- Tightened upstream repo bootstrap governance for empty Git repositories,
  starter public files, initial commit sequencing, and `commitLogs/` behavior.
- Expanded the bootstrap target from a harness-only baseline to a minimal
  usable open-source product shell with install docs, examples, and smoke
  testing.

## Questions Asked

- None recorded yet.

## Issues Raised

- Raised: The bootstrap workflow allowed copying the portable file set but did
  not define how an empty upstream Git repo gets a valid `HEAD`, starter public
  files, or its first commit.
  Resolution: Added empty-repo bootstrap requirements to the shared standard
  and chat workbench bootstrap workflow.

## Decisions Made

- Decision: Empty upstream repos need an initial branch, starter public files,
  and first commit before normal chat startup can be tested.
  Rationale: Chat startup and worktree helpers assume a usable Git branch and
  committed baseline.
- Decision: Do not copy source `commitLogs/` into an upstream repo.
  Rationale: The upstream repo should create its own session logs when its
  first chat starts.
- Decision: Bootstrap `llm-workbench` as a minimal usable product, not only a
  harness file baseline.
  Rationale: The open-source repo should be tested through the same docs,
  installer, example, and smoke-test surface an external engineer would use.

## Activity Log

### 2026-06-19T16:06:50Z - Session started

Initial intent: tighten upstream workbench bootstrap workflow for initial git setup and commitLogs behavior

### 2026-06-19T16:13:00Z - Bootstrap initial Git behavior documented

Updated the upstream repo bootstrap standard and chat workbench bootstrap
workflow so empty upstream repos establish `main`, starter public files, and an
initial commit before normal chat startup. Clarified that source `commitLogs/`
are excluded and the upstream repo creates its own logs on first chat startup.
Expanded the first bootstrap target to include public docs, examples,
install/uninstall scripts, and an install smoke test.

Verification:

- `bash scripts/shared/chat/audit-chat-layer-migration.sh`
- `bash scripts/shared/chat/request-initialization/check-classify-task-fixtures.sh`

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0015-use-shared-upstream-repo-bootstrap-standard.md
Reason: Updated ADR 0015 to capture the empty-upstream-repo first-commit
requirement and `commitLogs/` ownership rule.

## Session Metrics

Raised at UTC: 2026-06-19T16:06:50Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- None recorded yet.
