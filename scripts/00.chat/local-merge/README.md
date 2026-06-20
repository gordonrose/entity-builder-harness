<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain local merge readiness and visibility scripts.
domain: local-merge
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-promote-to-main.md
  - scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/README.md
-->

# Local Merge Scripts

Local merge scripts help decide whether chat work can be integrated into local
`main`. They are local coordination tools, not push tools.

Use this domain when checking whether a chat branch is current with `main`,
whether related chat branches are active, or whether overlapping chat work
needs human attention before promotion.

