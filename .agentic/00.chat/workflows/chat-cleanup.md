<!-- agentic-artifact:
owner: 00.chat
kind: workflow
purpose: Govern cleanup of chat branches, worktrees, temporary refresh artifacts, and empty session logs.
domain: cleanup
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/README.md
  - scripts/00.chat/git/cleanup-empty-chat-branches/script.sh
-->

# Chat Cleanup Workflow

## Use When

Use this when inspecting or cleaning chat branches, chat-owned worktrees,
temporary preflight worktrees, or empty session logs.

## Purpose

Own cleanup of chat branches, chat-owned worktrees, temporary preflight
worktrees, and empty session logs.

## Required Gates

Before deleting branches, removing worktrees, deleting logs, or discarding any
work, inspect chat workspace state:

```bash
bash scripts/00.chat/reporting/report-chat-workspaces/script.sh
```

For empty chat branch cleanup, start with a dry run:

```bash
bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --dry-run
```

Only run `--apply` after explicit user approval in the current chat:

```bash
bash scripts/00.chat/git/cleanup-empty-chat-branches/script.sh --apply
```

## Rules

- Never remove dirty worktrees automatically.
- Never delete logs with recorded commits or retention markers.
- Never delete the current branch.
- Never delete a branch checked out in any worktree.
- Delete empty session logs only when the matching branch is empty and the log
  names that branch.
- Delete deterministic temporary preflight branches/worktrees only when their
  corresponding operation has either been promoted or explicitly abandoned by
  the user.
- After a successful preflight promotion, automatically delete stale sibling
  preflight branches/worktrees for the same chat branch only when the stale
  branch is already an ancestor of the promoted chat branch and any associated
  worktree is clean.
- Report and skip stale sibling preflight branches that have unique commits,
  dirty worktrees, multiple worktrees, or ambiguous ownership.
- Require explicit approval for cleanup outside deterministic safe cases.
- If a cleanup case is not covered here or by a script-level gate, stop and ask
  whether to update the harness or approve a one-off exception.

## Script Paths

The canonical empty-branch cleanup script is:

```txt
scripts/00.chat/git/cleanup-empty-chat-branches/script.sh
scripts/00.chat/reporting/report-chat-workspaces/script.sh
```

The old shared cleanup path remains as a compatibility wrapper during the
script-layout migration. See ADR 0017 for compatibility-wrapper paths.

Other cleanup helpers:

```txt
scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh
```

## Migration Notes

When migrating script paths later, preserve:

- never remove dirty worktrees automatically
- never delete logs with recorded commits or retention markers
- delete only deterministic temporary preflight branches/worktrees
- require explicit approval for cleanup outside deterministic safe cases
