<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.rule-packs.readme
version: 1
status: active
layer: 03.product
domain: architecture
disciplines:
- agentic
- architecture
kind: rule-pack-readme
purpose: Define the product corpus home for product-owned task rule packs.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: product.corpus.readme
  path: docs/03.product/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Product Rule Packs

This directory contains task-shaped rule packs for product work.

Use owner topic subdirectories for product task packs:

- `apps/` for entity-builder and app/product composition tasks.
- `core/` for packages/core contract and primitive tasks.
- `design-system/` for design-system component tasks.
- `platform/` for platform adapter and runtime composition tasks.

Rule packs should reference the structured rules that govern the same task and
should remain task-shaped rather than becoming another layer rule.
