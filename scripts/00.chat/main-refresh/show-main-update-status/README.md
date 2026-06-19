<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain the local main update status report for chat branches.
domain: main-refresh
portability: llm-workbench-required
used_by:
  - scripts/00.chat/main-refresh/show-main-update-status/script.sh
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
