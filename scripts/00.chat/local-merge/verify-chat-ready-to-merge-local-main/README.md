<!-- agentic-artifact:
owner: 00.chat
kind: guide
purpose: Explain the read-only gate that checks whether a chat branch can merge into local main.
domain: local-merge
portability: llm-workbench-required
used_by:
  - scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh
  - scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh
-->

# Verify Chat Ready To Merge Local Main

This capability answers: can this completed chat branch be merged into local
`main` right now?

It is read-only. It checks the root integration worktree, the chat-owned
worktree, session-log metadata, branch freshness, dirty state, and recorded
commit evidence. If any requirement is missing, it prints a deterministic
blocked state and the recovery action to take before retrying.

Use this before an explicit local merge from a chat branch into `main`.
