<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain chat-owned Git maintenance scripts.
domain: git
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/workflows/chat-cleanup.md
  - scripts/00.chat/git/cleanup-empty-chat-branches/README.md
-->

# Git Scripts

Git scripts in this domain handle chat-owned Git maintenance. They are not
general-purpose Git wrappers. They exist only where chat lifecycle behavior
needs deterministic branch or log handling.

Destructive behavior must be explicit and governed. Scripts should default to
inspection or dry-run when deletion is possible.

