<!-- agentic-artifact:
schema: agentic-artifact/v2
id: chat.adrs.readme
version: 1
status: active
layer: 00.chat
domain: architecture
disciplines:
- agentic
- architecture
kind: adr-readme
purpose: Define the owner-aligned ADR home for chat lifecycle and portable workbench decisions.
portability:
  class: required
  targets:
  - llm-workbench
used_by:
- id: harness.adr.0032-use-owner-aligned-adr-roots
  path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- id: chat.docs.readme
  path: docs/00.chat/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 00.chat ADRs

This directory records durable architecture decisions owned by the chat layer:
chat lifecycle, session logs, chat-owned worktrees, portable workbench
bootstrap, upstream handoff, write-permission defaults, and commit readiness.

Use this root for chat-owned ADR history. Agent-facing chat workflows and
checklists stay under `.agentic/00.chat/`; public workbench documentation stays
under `docs/00.chat/`; generated or per-chat session logs stay under
`commitLogs/`.

The old prototype ADR pointers have been retired. Use this owner-aligned ADR
root directly for chat-owned decision history.
