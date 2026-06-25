<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.apply-rehearsed-refresh.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: guide
  purpose: Explain how the harness applies a rehearsed main refresh to a chat branch.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.apply-rehearsed-refresh
    path: scripts/00.chat/main-refresh/apply-rehearsed-refresh/script.sh
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
