# Chat Session: 2026-06-16-14-19 local-chat-worktree-strategy

<!-- agentic-session
id: 2026-06-16-14-19-i-have-about-15-staged-changes-are-they-not-committed-yet-gi
task: i have about 15 staged changes -are they not committed yet, given all my chats are committed?
branch: chat/2026-06-16-14-19-i-have-about-15-staged-changes-are-they-not-committed-yet-gi
layer: shared
mode: implementation
workflow: .agentic/shared/workflows/change-shared-process.md
status: ready
raised_at_utc: 2026-06-16T13:19:34Z
latest_commit_at_utc:
latest_commit_sha:
chat_duration:
estimated_tokens:
-->

## Initial Intent

i have about 15 staged changes -are they not committed yet, given all my chats are committed?

## Branch

`chat/2026-06-16-14-19-i-have-about-15-staged-changes-are-they-not-committed-yet-gi`

## Session Log

- Session started.
- Branch created.
- Commit log initialized.

## Questions Asked

- Why did staged changes remain after chats were committed?
- What does it mean for a branch to move forward?
- How do large engineering teams avoid this kind of local branch/worktree
  confusion?
- How should chat-based harness terminology map to feature-branch strategy?
- What changes are needed for multiple chats working in parallel on one device?

## Issues Raised

- The active root worktree had stale staged entries after commits made from an
  isolated worktree advanced the same chat branch. Resolution: unstaged the
  stale index state without changing file contents, restored protected tracked
  commit logs, and shifted the harness design from commit-only isolation to
  session-owned worktree isolation.
- Existing commit-log edits and untracked logs from other sessions remain in
  the root worktree. Resolution: preserved them rather than reverting unrelated
  user/session state.

## Decisions Made

- Treat the root repository worktree as a local integration console, not as the
  default place for chat task writes.
- Treat each chat as a local developer-like work actor with its own chat branch,
  chat-owned worktree, index, and session log.
- Make root task writes deterministically fail with a write-location guard.
- Add a local convergence workflow as the harness equivalent of a PR/merge lane
  into local `main`.
- Report branch freshness against `main`; require explicit approval before
  merge, rebase, promotion to `main`, push, destructive cleanup, or history
  rewrite.
- Preserve commit logs that record work or retention markers.

## Activity Log

### 2026-06-16T13:19:34Z - Session started

Initial intent: i have about 15 staged changes -are they not committed yet, given all my chats are committed?

### 2026-06-16T16:26:04Z - Local chat worktree strategy implemented

Reconciled the stale staged index, restored protected historical commit logs,
updated chat start to create a chat-owned worktree without switching the root
worktree, added write-location and freshness gates, added a local convergence
workflow, and added smoke coverage for the new chat worktree startup invariant.

## Commits

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0011-use-chat-owned-worktrees-for-local-convergence.md
Reason: The harness branching strategy changed from commit-boundary isolation
to session-owned worktree isolation with a local convergence lane.

## Session Metrics

Raised at UTC: 2026-06-16T13:19:34Z
Latest commit at UTC:
Latest commit SHA:
Chat duration:
Estimated tokens:

## Notes

- None recorded yet.
