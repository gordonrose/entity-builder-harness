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
bash scripts/shared/chat/report-chat-workspaces.sh
```

For empty chat branch cleanup, start with a dry run:

```bash
bash scripts/shared/git/cleanup-empty-chat-branches.sh --dry-run
```

Only run `--apply` after explicit user approval in the current chat:

```bash
bash scripts/shared/git/cleanup-empty-chat-branches.sh --apply
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
- Require explicit approval for cleanup outside deterministic safe cases.
- If a cleanup case is not covered here or by a script-level gate, stop and ask
  whether to update the harness or approve a one-off exception.

## Compatibility Scripts

The executable scripts still live under compatibility paths:

```txt
scripts/shared/git/cleanup-empty-chat-branches.sh
scripts/shared/chat/report-chat-workspaces.sh
scripts/shared/git/promote-preflight-refresh.sh
```

## Migration Notes

When migrating script paths later, preserve:

- never remove dirty worktrees automatically
- never delete logs with recorded commits or retention markers
- delete only deterministic temporary preflight branches/worktrees
- require explicit approval for cleanup outside deterministic safe cases
