<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain how the harness rehearses refreshing a chat branch from main before applying it.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh
  - scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh
-->

# Rehearse Refresh From Main

This capability answers: would refreshing this chat branch from `main` work
safely?

It creates a temporary preflight branch and worktree from the current chat
branch, then merges the base branch there. The active chat worktree is left
untouched. If the merge succeeds, the temporary branch contains the tested merge
result and can be applied with `apply-rehearsed-refresh`.

Use this when a chat branch has real work and a direct refresh would be too
risky to perform without rehearsal.
