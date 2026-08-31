<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adr.0022-add-rag-rulebook-layer.pointer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: compatibility-pointer
purpose: Point older ADR 0022 references to the RAG/rulebook-layer canonical ADR.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# ADR 0022 Moved

The canonical ADR now lives at
`docs/02.rag-rulebook/adrs/0022-add-rag-rulebook-layer.md`.

This compatibility pointer exists while the prototype architecture ADR corpus
is split into owner-aligned ADR roots.
