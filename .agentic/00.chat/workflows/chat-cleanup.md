# Chat Cleanup Workflow

## Purpose

Own cleanup of chat branches, chat-owned worktrees, temporary preflight
worktrees, and empty session logs.

## Current Implementation

Cleanup behavior is still split across compatibility scripts:

```txt
scripts/shared/git/cleanup-empty-chat-branches.sh
scripts/shared/chat/report-chat-workspaces.sh
scripts/shared/git/promote-preflight-refresh.sh
```

Follow the relevant script-level gates until this workflow is promoted to full
implementation.

## Migration Notes

When migrating, preserve:

- never remove dirty worktrees automatically
- never delete logs with recorded commits or retention markers
- delete only deterministic temporary preflight branches/worktrees
- require explicit approval for cleanup outside deterministic safe cases
