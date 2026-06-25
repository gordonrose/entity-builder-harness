<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.recovery.readme
  version: 1
  status: active
  layer: 00.chat
  domain: recovery
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain recovery scripts for wrong-worktree chat edits.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-commit
    path: .agentic/00.chat/workflows/chat-commit.md
  - id: chat.script.recovery.import-active-paths-to-chat-worktree.readme
    path: scripts/00.chat/recovery/import-active-paths-to-chat-worktree/README.md
-->
# Recovery Scripts

Recovery scripts handle exceptional chat lifecycle situations, especially work
that was edited in the wrong checkout.

Normal task work should happen directly in the chat-owned worktree. Recovery
scripts exist so explicit paths can be moved back into the right worktree
without normalizing broad or ambiguous repair actions.

