# Chat Start Workflow

## Purpose

Own chat startup, active session discovery, chat-owned worktree selection, and
startup blocked states.

## Current Implementation

The executable compatibility workflow is still:

```txt
.agentic/shared/workflows/chat-start-interview.md
```

Follow that workflow until this file is promoted from ownership entrypoint to
full implementation.

This file is the canonical chat-start entrypoint. `AGENTS.md` points here so
future agents discover chat lifecycle ownership before following the legacy
compatibility implementation.

## Migration Notes

When migrating, preserve:

- session metadata as first source of truth
- no reclassification when metadata is complete
- exact missing-session and dirty-worktree blocked responses
- chat-owned worktree verification before writes
