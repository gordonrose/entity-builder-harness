<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.migration.readme
  version: 1
  status: active
  layer: 00.chat
  domain: migration
  disciplines:
  - agentic
  kind: script-domain-readme
  purpose: Explain migration audit scripts for the chat layer.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.migration-plan
    path: .agentic/00.chat/migration-plan.md
  - id: chat.script.migration.audit-chat-layer-migration.readme
    path: scripts/00.chat/migration/audit-chat-layer-migration/README.md
-->
# Migration Scripts

Migration scripts check whether the chat lifecycle layer still depends on old
locations. They are guardrails for moving behavior into canonical
`.agentic/00.chat` and `scripts/00.chat` surfaces.

Use this domain when changing ownership, moving compatibility paths, or
preparing the harness for a standalone workbench repo.

