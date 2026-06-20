<!-- agentic-artifact:
owner: 00.chat
kind: capability-readme
purpose: Explain the chat layer migration audit.
domain: migration
portability: llm-workbench-required
used_by:
  - .agentic/00.chat/migration-plan.md
  - scripts/00.chat/migration/audit-chat-layer-migration/script.sh
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
