# Chat Promote To Main Workflow

## Purpose

Own local convergence from completed chat branches into local `main`.

## Current Implementation

The executable compatibility workflow is still:

```txt
.agentic/shared/workflows/local-convergence.md
```

Follow that workflow until this file is promoted from ownership entrypoint to
full implementation.

## Migration Notes

When migrating, preserve:

- root worktree as local integration console
- chat worktree cleanliness before promotion
- freshness checks against local `main`
- explicit user approval before merging into `main`
- separate explicit approval for pushes
- historical retention of session logs with recorded commits
