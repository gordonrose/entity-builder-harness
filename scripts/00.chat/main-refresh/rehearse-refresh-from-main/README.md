<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.rehearse-refresh-from-main.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: guide
  purpose: Explain how the harness rehearses refreshing a chat branch from main before
    applying it.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.rehearse-refresh-from-main
    path: scripts/00.chat/main-refresh/rehearse-refresh-from-main/script.sh
  - id: chat.script.main-refresh.rehearse-refresh-from-main.smoke-test
    path: scripts/00.chat/main-refresh/rehearse-refresh-from-main/smoke-test.sh
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
