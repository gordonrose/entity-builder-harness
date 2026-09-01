<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.corpus.readme
version: 1
status: active
layer: 06.shared
domain: governance
disciplines:
- agentic
- architecture
kind: corpus-readme
purpose: Define the RAG-readable shared corpus boundary for deliberately cross-layer source material and rules.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.document-artifact-placement
  path: .agentic/01.harness/standards/document-artifact-placement.md
- id: rag-rulebook.standard.domain-corpus-package
  path: .agentic/02.rag-rulebook/standards/domain-corpus-package.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 06.shared Corpus

This directory is the RAG-readable shared corpus package for
`corpus.06.shared`.

The governing workflows and standards for shared process primitives live under
`.agentic/shared/`. This directory contains human-readable corpus material,
shared ADRs, and structured rules that intentionally apply across multiple
numbered layers.

Use this corpus for cross-layer rules only when the rule cannot honestly be
owned by chat, harness, RAG/rulebook, product, deploy, or education alone.

Prefer a narrower layer corpus when one owner can make and validate the
decision. Shared placement should be deliberate because shared rules tend to
create broad coupling.

Shared ADRs live in `adrs/`. Shared structured rules live under `rules/`.

The legacy prototype architecture corpus has been retired after its content
moved to owner-aligned roots.
