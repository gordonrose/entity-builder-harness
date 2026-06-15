# 0005 Preserve Bootstrap Dirty Worktree Before Workflow Loading

Status: accepted
Date: 2026-06-16

## Context

New chat startup creates a branch and session log for the next agent. If the
worktree is already dirty before that branch is created, those changes may
belong to the user, a previous session, or a partially completed operation.

The normal chat-start flow asks the agent to load session metadata and the
selected workflow before acting. That is useful when the inherited state is
clean, but it can be too much when the worktree was already dirty: even
additional inspection can blur whether later state came from startup, the
agent, or pre-existing user work.

## Decision

Chat startup records the bootstrap worktree status before switching to the new
chat branch and includes that status in the first prompt.

When the bootstrap status is dirty, the first agent response must be the
standard dirty-worktree blocked response for the resolved layer, mode, and
workflow. The agent must not read workflows, run `git status`, or run the
dirty-worktree gate before giving that blocked response.

When the bootstrap status is clean, the agent may continue with normal
chat-start workflow loading and gates.

## Consequences

Inherited dirty state is protected before an agent gathers more context or
performs additional git inspection. This makes the initial blocked response
depend on state captured by startup, not on state that may have changed after
branch creation.

The first prompt becomes more prescriptive, and agents must honor the bootstrap
status even when they would otherwise prefer to inspect the repo first.
