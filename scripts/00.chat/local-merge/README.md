<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.local-merge.readme
  version: 1
  status: active
  layer: 00.chat
  domain: local-merge
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain local merge readiness and visibility scripts.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-promote-to-main
    path: .agentic/00.chat/workflows/chat-promote-to-main.md
  - id: chat.script.local-merge.verify-chat-ready-to-merge-local-main.readme
    path: scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/README.md
-->
# Local Merge Scripts

Local merge scripts help decide whether chat work can be integrated into local
`main`. They are local coordination tools, not push tools.

Use this domain when checking whether a chat branch is current with `main`,
whether related chat branches are active, or whether overlapping chat work
needs human attention before promotion.

