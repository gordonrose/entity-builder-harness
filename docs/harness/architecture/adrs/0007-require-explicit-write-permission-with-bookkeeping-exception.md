# 0007 Require Explicit Write Permission With Bookkeeping Exception

Status: accepted
Date: 2026-06-16

## Context

The harness is designed for collaborative work in a shared repository. Agents
often need to inspect files before the user has decided whether to authorize
changes. At the same time, chat sessions maintain durable bookkeeping in the
current session log and aggregate commit-log summary.

Requiring explicit approval for every routine bookkeeping update creates noisy
repeat prompts after the user has already granted write permission for the
chat. Allowing broad writes after one approval would be unsafe because task
commits, branch operations, history rewrites, pushes, and destructive actions
carry different risks.

ADR 0001 records the requirement to preserve session decisions before commit.
This ADR codifies the write-permission boundary around that session
bookkeeping.

## Decision

The default mode is read-only. Agents must not create, edit, move, delete,
stage, commit, format, or patch files unless the user explicitly grants write
permission in the current chat.

After explicit write permission has been granted for the chat, routine session
bookkeeping may be staged and checkpointed without another prompt only when it
is limited to:

- the current chat session log
- `commitLogs/README.md`

Task commits still require explicit user approval. Destructive git operations,
branch deletion, history rewrites, pushes, discarding work, and overwriting work
still require explicit user approval.

Scripts and gates enforce the bookkeeping exception by rejecting checkpoint
commits when any non-bookkeeping path is dirty or staged.

## Consequences

The harness reduces repetitive approval prompts for narrow session maintenance
while preserving a strict boundary around code, process, and git history
changes.

The exception is intentionally small. If future bookkeeping expands beyond the
current session log and aggregate summary, the allowed scope must be revisited
instead of assumed.
