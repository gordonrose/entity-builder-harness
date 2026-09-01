<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.source-material.readme
version: 1
status: active
layer: 03.product
domain: requirements
disciplines:
- agentic
- architecture
kind: source-material-readme
purpose: Define the product source-material corpus home for product architecture guides and rule derivation inputs.
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
# Product Source Material

This directory contains RAG-readable product source material for product
architecture, runtime contracts, packages/core, platform, apps, frontend, and
design-system decisions.

Use `core/` for packages/core contract source material.
Use `platform/` for platform runtime, platform contracts, and platform adapter
source material.
Use `guides/` for long-form product architecture guides and their preserved
original files.

Structured product rules derived from this material live under
`docs/03.product/rules/`.
