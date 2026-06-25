<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: chat.script.migration.audit-chat-layer-migration.readme
  version: 1
  status: active
  layer: 00.chat
  domain: migration
  disciplines:
  - agentic
  kind: capability-readme
  purpose: Explain the chat layer migration audit.
  portability:
    class: required
    targets:
    - llm-workbench
  used_by:
  - id: chat.migration-plan
    path: .agentic/00.chat/migration-plan.md
  - id: chat.script.migration.audit-chat-layer-migration
    path: scripts/00.chat/migration/audit-chat-layer-migration/script.sh
-->
# Audit Chat Layer Migration

`script.sh` checks that the canonical chat-layer files exist, retired
compatibility paths stay absent, and retired compatibility references do not
return to active process files.

The audit distinguishes current canonical requirements from historical or
policy references. It does not treat old session logs as migration blockers.

Use this after moving workflows, checklists, standards, or scripts so the next
agent can see whether the chat layer still relies on retired compatibility
paths.
