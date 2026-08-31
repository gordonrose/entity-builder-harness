<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.architecture.rules.pointer
version: 1
status: active
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: compatibility-pointer
purpose: Point older prototype rule references toward owner-aligned corpus rule roots during the domain split.
portability:
  class: source-only
  targets: []
used_by:
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Prototype Rules Split In Progress

The prototype architecture rules root is being split by owner corpus.

Product rules now live under `docs/03.product/rules/`. Remaining files in this
legacy root are deploy, harness, or shared candidates that will move in a later
governed slice.

This compatibility pointer exists while the prototype architecture corpus is
split into numbered owner-aligned homes.
