<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.local-merge.verify-chat-ready-to-merge-local-main.readme
  version: 1
  status: active
  layer: 00.chat
  domain: local-merge
  disciplines:
  - agentic
  kind: guide
  purpose: Explain the read-only gate that checks whether a chat branch can merge into
    local main.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.script.local-merge.verify-chat-ready-to-merge-local-main
    path: scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/script.sh
  - id: chat.script.local-merge.verify-chat-ready-to-merge-local-main.smoke-test
    path: scripts/00.chat/local-merge/verify-chat-ready-to-merge-local-main/smoke-test.sh
-->
# Verify Chat Ready To Merge Local Main

This capability answers: can this completed chat branch be merged into local
`main` right now?

It is read-only. It checks the root integration worktree, the chat-owned
worktree, session-log metadata, branch freshness, dirty state, and recorded
commit evidence. If any requirement is missing, it prints a deterministic
blocked state and the recovery action to take before retrying.

Use this before an explicit local merge from a chat branch into `main`.
