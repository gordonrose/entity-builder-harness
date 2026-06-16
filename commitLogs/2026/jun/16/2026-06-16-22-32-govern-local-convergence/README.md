# Chat Session: 2026-06-16-22-32 govern-local-convergence

<!-- agentic-session
id: 2026-06-16-22-32-update-harness-to-add-governed-approach-to-merging-to-local-
task: update harness to add governed approach to merging to local main when chat work is complete
branch: chat/2026-06-16-22-32-update-harness-to-add-governed-approach-to-merging-to-local-
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-16-22-32-update-harness-to-add-governed-approach-to-merging-to-local--2068012364
layer: shared
mode: planning
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-16T21:32:52Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_tokens:
-->

## Initial Intent

update harness to add governed approach to merging to local main when chat work is complete

## Branch

`chat/2026-06-16-22-32-update-harness-to-add-governed-approach-to-merging-to-local-`

## Worktree

`/tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-16-22-32-update-harness-to-add-governed-approach-to-merging-to-local--2068012364`

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- Should local convergence verify session logs that exist only on the chat
  branch? Yes, by using Git branch object reads instead of filesystem-only
  checks from root `main`.
- Should behind, diverged, and dirty chat worktree states get governed recovery
  paths now? Yes, as conservative blocked states with explicit approval before
  any Git-changing recovery.

## Issues Raised

- `local-convergence.md` pointed to `ensure-chat-worktree.sh <session-log>`,
  but that script requires the log to exist in the current filesystem. During
  promotion, the log may exist only on the chat branch.
- The first patch attempt landed in the root integration worktree instead of
  this chat-owned worktree. Those root edits were removed, and the intended
  changes were applied in the chat-owned worktree.

## Decisions Made

- Add a read-only local convergence verifier instead of expanding
  `ensure-chat-worktree.sh` beyond its filesystem-log responsibility.
- Keep merge-to-main as an explicit approved manual step after verification.
- Govern `behind`, `diverged`, and `dirty chat worktree` states as blocked
  states. Refreshes prefer merging `main` into the chat branch from the
  chat-owned worktree; rebases remain separately approval-bound.
- No new ADR is needed for this change because it implements the existing
  local convergence and missing-governance direction in workflow and script
  form.

## Activity Log

### 2026-06-16T21:32:52Z - Session started

Initial intent: update harness to add governed approach to merging to local main when chat work is complete

### 2026-06-16T22:01:36Z - Local convergence verifier implemented

- Added `scripts/shared/git/verify-local-convergence.sh` as a read-only
  preflight that can inspect branch-only session logs and classify blocked
  merge-to-main states.
- Updated `.agentic/shared/workflows/local-convergence.md` to require the
  verifier and document governed recovery for behind, diverged, dirty,
  missing, and ambiguous evidence states.
- Added `scripts/shared/git/smoke-test-local-convergence-verifier.sh` covering
  eligible, behind, diverged, dirty chat worktree, missing log, missing
  worktree, and log-head mismatch states.
- Verification run:
  `bash scripts/shared/git/smoke-test-local-convergence-verifier.sh`
  passed.
- Verification run:
  `bash scripts/shared/harness/check-deterministic-process-drift.sh --paths .agentic/shared/workflows/local-convergence.md`
  passed.

## Commits

- None recorded yet.

## ADR Disposition

ADR needed: no
ADR path:
Reason: The change codifies an existing local convergence policy gap with a
read-only verifier and workflow recovery rules; it does not introduce a new
durable architecture decision beyond existing missing-governance and
chat-worktree decisions.

## Session Metrics

Raised at UTC: 2026-06-16T21:32:52Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated tokens:

## Notes

- None recorded yet.
