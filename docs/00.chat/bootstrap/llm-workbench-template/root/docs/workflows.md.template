# Workflows

## Start A Chat

Chat startup is governed by:

```txt
.agentic/00.chat/workflows/chat-start.md
```

At startup the harness finds or creates session metadata, selects the workflow,
and verifies the chat-owned worktree when writes are allowed.

## Commit Work

Commit preparation is governed by:

```txt
.agentic/00.chat/workflows/chat-commit.md
```

The before-commit gates check prerequisites, session log safety, deterministic
process drift, metadata headers, and governed command drift.

## Refresh From Main

Main refresh is governed by:

```txt
.agentic/00.chat/workflows/chat-refresh-from-main.md
```

The workflow separates read-only status, rehearsal, and apply.

## Promote To Main

Promotion is governed by:

```txt
.agentic/00.chat/workflows/chat-promote-to-main.md
```

The harness treats local merge readiness separately from remote push. A push
always needs separate explicit approval.

## Report Or Close A Chat

Reporting and closeout are governed by:

```txt
.agentic/00.chat/workflows/chat-reporting.md
.agentic/00.chat/workflows/chat-cleanup.md
```

These workflows help summarize work, inspect active workspaces, and clean up
empty chat branches when it is safe.
