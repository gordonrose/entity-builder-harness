<!-- agentic-artifact:
owner: 00.chat
kind: script-domain-readme
purpose: Explain migration audit scripts for the chat layer.
domain: migration
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/migration-plan.md
  - scripts/00.chat/migration/audit-chat-layer-migration/README.md
-->

# Migration Scripts

Migration scripts check whether the chat lifecycle layer still depends on old
locations. They are guardrails for moving behavior into canonical
`.agentic/00.chat` and `scripts/00.chat` surfaces.

Use this domain when changing ownership, moving compatibility paths, or
preparing the harness for a standalone workbench repo.

