# Chat Session: 2026-06-23-18-51 prevent-accidental-reuse-of-old-chat-worktrees

<!-- agentic-session
id: 2026-06-23-18-51-prevent-accidental-reuse-of-old-chat-worktrees
task: prevent accidental reuse of old chat worktrees
branch: chat/2026-06-23-18-51-prevent-accidental-reuse-of-old-chat-worktrees
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-23-18-51-prevent-accidental-reuse-of-old-chat-worktrees-2470436670
layer: harness
mode: implementation
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-23T17:51:05Z
codex_session_log_path:
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_chat_tokens:
estimated_chat_cost:
estimated_chat_cost_basis:
-->

## Initial Intent

prevent accidental reuse of old chat worktrees

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

- The chat startup fast path must not silently reuse a session that already has
  recorded commits.
- Explicit continuation approval is required before using metadata from an
  existing recorded chat session and worktree.

## Activity Log

### 2026-06-23T17:51:05Z - Session started

Initial intent: prevent accidental reuse of old chat worktrees

## Commits

- None recorded yet.

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0006-use-session-metadata-for-routing-after-chat-start.md
Reason: Updated the existing session-metadata routing ADR to cover the recorded-session reuse boundary.

## Session Metrics

Raised at UTC: 2026-06-23T17:51:05Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated chat tokens:
Estimated chat cost:
Estimated chat cost basis:

## Notes

- Classifier result corrected with user approval: layer `harness`, mode
  `implementation`, workflow `.agentic/01.harness/workflows/change-harness.md`.
- Implementation direction: make `read-current-chat-log` refuse recorded
  sessions by default and require an explicit `--allow-recorded-session` flag
  after user approval.
