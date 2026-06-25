<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.main-refresh.show-main-update-status.readme
  version: 1
  status: active
  layer: 00.chat
  domain: main-refresh
  disciplines:
  - agentic
  kind: guide
  purpose: Explain the local main update status report for chat branches.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.main-refresh.show-main-update-status
    path: scripts/00.chat/main-refresh/show-main-update-status/script.sh
-->
# Show Main Update Status

This read-only capability answers: has local `main` moved relative to the chat
branches?

It prints each local branch's ahead/behind count relative to the selected base
branch, defaulting to `main`. It does not fetch, merge, rebase, stage, or write
files. If remotes exist, it reminds the operator to fetch before treating the
comparison as current.

Use this near the start of a main-refresh conversation so the human and agent
share the same branch map before choosing a refresh path.
