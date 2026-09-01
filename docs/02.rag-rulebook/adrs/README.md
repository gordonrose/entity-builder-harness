<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.adrs.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: architecture
disciplines:
- agentic
- architecture
kind: adr-readme
purpose: Define the owner-aligned ADR home for RAG/rulebook architecture decisions.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.adr.0032-use-owner-aligned-adr-roots
  path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- id: rag-rulebook.corpus.readme
  path: docs/02.rag-rulebook/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 02.rag-rulebook ADRs

This directory records durable architecture decisions owned by the
RAG/rulebook layer: corpus packaging, source-to-rule conversion, recognition
sources, retrieval policy, context packets, chunking, indexing, and portable
RAG service boundaries.

Use this root for RAG/rulebook-owned ADRs that are corpus history. Agent-facing
workflows, policies, schemas, validators, and service implementation plans stay
under `.agentic/02.rag-rulebook/`.

The old prototype ADR pointers have been retired. Use this owner-aligned ADR
root directly for RAG/rulebook decision history.
