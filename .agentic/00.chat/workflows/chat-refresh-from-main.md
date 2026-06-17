# Chat Refresh From Main Workflow

## Purpose

Own refreshing active chat branches from the accepted `main` baseline.

## Current Implementation

The executable compatibility workflow is still:

```txt
.agentic/shared/workflows/main-updated.md
```

Follow that workflow until this file is promoted from ownership entrypoint to
full implementation.

## Migration Notes

When migrating, preserve:

- dirty-state classification before refresh
- checkpoint-before-refresh behavior for normal repo work
- preflight refresh in a temporary worktree before mutating the chat worktree
- stash exclusion unless a future governed stash capability exists
- missing-governance blocked behavior for unsupported conflict resolution
