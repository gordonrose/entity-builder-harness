<!-- agentic-artifact:
owner: harness
kind: adr
purpose: Record the older isolated worktree commit-boundary model and its recovery-only successor behavior.
domain: architecture
portability: llm-workbench-required
used_by:
  - scripts/shared/git/with-chat-branch.sh
  - scripts/00.chat/recovery/import-active-paths-to-chat-worktree/README.md
-->

# 0009 Use Isolated Worktrees for Session Commit Boundaries

Status: accepted, superseded for normal chat work by ADR 0011
Date: 2026-06-16

Superseded normal path: ADR 0011 changed the harness from
commit-boundary-only isolated worktrees to chat-owned worktrees for all task
work. The useful part of this ADR remains as governed recovery/import behavior:
explicit paths can be imported from an active worktree into the session's
chat-owned worktree when edits happened in the wrong checkout.

## Context

Each chat session records its intended `chat/*` branch in the session log, but
multiple chats and writing tasks can share one local checkout. Commit gates,
staging, commits, commit recording, and session-log checkpoint commits need to
operate against the session branch without disturbing unrelated dirty work in
the active user worktree.

An earlier helper design switched the active worktree to the session branch,
ran a command, and switched back. That was better than manual branch
coordination, but it still exposed unrelated work to branch-switch conflicts and
made the user's checkout move during commit-boundary operations.

## Decision

Approved commit-boundary operations run through:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- <command> [args...]
```

This was the normal commit-boundary model when this ADR was accepted. For new
normal task work, use the chat-owned worktree recorded in the session log
instead.

The helper reads the branch from the session log, validates that it is a local
`chat/*` branch, and runs the requested command inside a deterministic isolated
worktree for that branch. The default worktree root is under
`${AGENTIC_CHAT_WORKTREE_ROOT:-/tmp/agentic-chat-worktrees/...}`. The same repo
path and branch resolve to the same reusable worktree path.

The helper must not switch, stage, clean, discard, or otherwise mutate the
active user worktree. If the active user worktree is already on the target
session branch, the helper may use Git's duplicate checkout force flag to create
the isolated worktree for that same branch while leaving active files and index
state alone. It stops if the session log is missing, branch metadata is missing,
the branch is not a local `chat/*` branch, the branch is already checked out in
another non-active worktree, the isolated path is invalid, or the wrapped
command fails.

Reuse is intentional. The helper leaves the isolated worktree in place so
approved staging and task commit steps can happen across multiple
commit-boundary commands. Cleanup is manual and requires explicit user approval.

When active-worktree edits need to become an approved task commit, agents mirror
only explicit approved paths into the isolated worktree with:

```bash
bash scripts/shared/git/with-chat-branch.sh <session-log> -- bash scripts/shared/git/stage-active-worktree-paths.sh <path>...
```

Current recovery import uses the clearer canonical capability:

```bash
bash scripts/00.chat/recovery/import-active-paths-to-chat-worktree/script.sh \
  --session-log <session-log> \
  --source-worktree <active-worktree> \
  -- <path>...
```

The staging helper accepts repository-relative paths, copies existing files or
directories from the active worktree into the isolated worktree, and stages
deletions when an approved path no longer exists in the active worktree.

This authorization is limited to commit preparation, staging for approved
commits, task commits after explicit approval, commit recording, and narrow
session-bookkeeping checkpoint commits. It does not authorize pushes, merges,
rebases, branch deletion, history rewrite, discarding work, or destructive
actions.

## Consequences

Dirty active worktrees no longer block commit-boundary work for other session
branches merely because branch switching would conflict. The session log becomes
the source of branch intent, and the isolated worktree becomes the place where
commit-boundary state lives.

The tradeoff is that reusable isolated worktrees can retain staged or dirty
state after an interrupted command. That state is intentionally preserved for
inspection and follow-up; agents must not clean it automatically. If an isolated
worktree becomes invalid or needs pruning, the user must explicitly approve the
cleanup.

Git normally allows a branch to be checked out by only one worktree at a time.
The helper uses a narrow duplicate-checkout exception only when the duplicate is
the active repo root for the same chat branch. If the target session branch is
already checked out in another non-active worktree, the helper stops instead of
adding another checkout.
