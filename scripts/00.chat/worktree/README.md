<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.worktree.readme
  version: 1
  status: active
  layer: 00.chat
  domain: worktree
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain chat-owned worktree scripts and helpers.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-start
    path: .agentic/00.chat/workflows/chat-start.md
  - id: chat.script.worktree.ensure-chat-worktree.readme
    path: scripts/00.chat/worktree/ensure-chat-worktree/README.md
-->
# Worktree Scripts

Worktree scripts keep chat task work in the right checkout. The root worktree is
the integration console; each chat should edit in its own sibling worktree.

This domain provides path helpers, write-location checks, dirty-state checks,
and worktree creation/verification.

The goal is not to make Git clever. The goal is to prevent accidental edits in
the wrong place.

