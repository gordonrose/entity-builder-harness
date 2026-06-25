<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.local-merge.list-active-chat-branches.readme
  version: 1
  status: active
  layer: 00.chat
  domain: local-merge
  disciplines:
  - agentic
  kind: guide
  purpose: Explain the read-only report that lists active chat branches before local
    merge decisions.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.local-merge.list-active-chat-branches
    path: scripts/00.chat/local-merge/list-active-chat-branches/script.sh
-->
# List Active Chat Branches

This capability answers: which chat branches are active, and how do they relate
to local `main`?

It prints chat branches, ahead/behind relation to the base branch, and available
session metadata such as layer, mode, status, and task. It is read-only and is
useful before choosing whether to refresh, merge, clean up, or inspect a chat
branch.
