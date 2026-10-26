<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: chat.script.local-merge.verify-chat-ready-to-merge-local-main.readme
  version: 1
  status: active
  created_on: "2026-06-19"
  updated_on: "2026-10-26"
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

It checks the root integration worktree, the chat-owned
worktree, session-log metadata, branch freshness, dirty state, and recorded
commit evidence. If any requirement is missing, it prints a deterministic
blocked state and the recovery action to take before retrying.

When this repository supplies the selector, the gate also executes affected
local integration checks in the clean chat worktree containing the base. It
reuses matching private receipts and may write temporary check outputs and cache
records. Package and provider operations remain outside local execution.
Required proof failure or branch/worktree drift blocks promotion. Portable
installations without the repository extension retain lifecycle checks.

Use this before an explicit local merge from a chat branch into `main`.

When the delivery census owner exists, promotion reconciles its current physical
entrypoints before accepting reusable integration receipts, matching the independent
CI source-coverage gate. A missing or failing census blocks promotion.
