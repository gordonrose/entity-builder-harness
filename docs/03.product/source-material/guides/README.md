<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.source-material.guides.readme
version: 1
status: active
layer: 03.product
domain: architecture
disciplines:
- agentic
- architecture
kind: source-material-readme
purpose: Define the product guide source-material track for long-form architecture guides and original source files.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: product.source-material.readme
  path: docs/03.product/source-material/README.md
-->
# Product Architecture Guides

Use `markdown/` for RAG-readable guide derivatives.
Use `originals/` for preserved original files that the Markdown guides cite as
source evidence.
