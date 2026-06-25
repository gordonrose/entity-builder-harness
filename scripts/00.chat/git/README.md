<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.git.readme
  version: 1
  status: active
  layer: 00.chat
  domain: git
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain chat-owned Git maintenance scripts.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.workflows.chat-cleanup
    path: .agentic/00.chat/workflows/chat-cleanup.md
  - id: chat.script.git.cleanup-empty-chat-branches.readme
    path: scripts/00.chat/git/cleanup-empty-chat-branches/README.md
-->
# Git Scripts

Git scripts in this domain handle chat-owned Git maintenance. They are not
general-purpose Git wrappers. They exist only where chat lifecycle behavior
needs deterministic branch or log handling.

Destructive behavior must be explicit and governed. Scripts should default to
inspection or dry-run when deletion is possible.

