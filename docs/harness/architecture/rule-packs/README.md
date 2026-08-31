<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.rule-packs.pointer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: compatibility-pointer
purpose: Point older prototype rule-pack references to the product rule-pack corpus.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Prototype Rule Packs Moved

Product task rule packs now live under `docs/03.product/rule-packs/`.

This compatibility pointer exists while the prototype architecture corpus is
split into numbered owner-aligned homes.
