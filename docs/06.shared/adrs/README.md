<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.adrs.readme
version: 1
status: active
layer: 06.shared
domain: architecture
disciplines:
- agentic
- architecture
kind: adr-readme
purpose: Define the owner-aligned ADR home for deliberately cross-layer shared decisions.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.adr.0032-use-owner-aligned-adr-roots
  path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- id: shared.corpus.readme
  path: docs/06.shared/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 06.shared ADRs

This directory records durable architecture decisions that are deliberately
cross-layer shared process rather than chat-only, harness-only, product-only,
RAG-only, deploy-only, or education-only decisions.

Use this root when the decision defines a reusable primitive that multiple
layers must apply. Prefer a narrower numbered ADR root when one layer can own,
validate, and evolve the decision.

During the prototype corpus migration, older shared ADRs may retain pointer
files under `docs/harness/architecture/adrs/` until active references have
been updated or retired.
