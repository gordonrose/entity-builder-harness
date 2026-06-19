<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain the read-only report that lists active chat branches before local merge decisions.
domain: local-merge
portability: llm-workbench-required
used_by:
  - scripts/00.chat/local-merge/list-active-chat-branches/script.sh
-->

# List Active Chat Branches

This capability answers: which chat branches are active, and how do they relate
to local `main`?

It prints chat branches, ahead/behind relation to the base branch, and available
session metadata such as layer, mode, status, and task. It is read-only and is
useful before choosing whether to refresh, merge, clean up, or inspect a chat
branch.
