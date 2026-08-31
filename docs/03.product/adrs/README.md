<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.adrs.readme
version: 1
status: active
layer: 03.product
domain: architecture
disciplines:
- architecture
kind: adr-readme
purpose: Define the owner-aligned ADR home for product and runtime contract decisions.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.adr.0032-use-owner-aligned-adr-roots
  path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 03.product ADRs

This directory records durable architecture decisions owned by the product
layer: product composition, app integration boundaries, provider-neutral
runtime contracts, packages/core contracts, and platform contract surfaces.

Use this root for product-owned ADRs that are corpus history. Product
workflows, standards, and implementation plans stay under `.agentic/03.product/`.
Product source material, structured rules, and rule packs stay under the
matching `docs/03.product/` corpus subdirectories.

During the prototype corpus migration, older product ADRs may retain pointer
files under `docs/harness/architecture/adrs/` until active references have
been updated or retired.
