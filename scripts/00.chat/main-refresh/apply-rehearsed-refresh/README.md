<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain how the harness applies a rehearsed main refresh to a chat branch.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh
-->

# Apply Rehearsed Refresh

This capability answers: the refresh rehearsal worked, so how do we apply that
tested result to the real chat branch?

It fast-forwards the current chat branch to the tested preflight branch, checks
that the expected commit was applied, removes the temporary preflight worktree,
deletes the preflight branch, and cleans up stale sibling preflight branches
when they are already ancestors of the promoted chat branch.

It refuses to run if the active chat worktree is dirty, the preflight worktree
is dirty, the branch is not a preflight branch, or the preflight branch no
longer descends from the current chat branch.
