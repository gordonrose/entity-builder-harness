<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain recovery scripts for wrong-worktree chat edits.
domain: recovery
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-commit.md
  - scripts/00.chat/recovery/import-active-paths-to-chat-worktree/README.md
-->

# Recovery Scripts

Recovery scripts handle exceptional chat lifecycle situations, especially work
that was edited in the wrong checkout.

Normal task work should happen directly in the chat-owned worktree. Recovery
scripts exist so explicit paths can be moved back into the right worktree
without normalizing broad or ambiguous repair actions.

