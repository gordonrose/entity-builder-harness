<!-- agentic-artifact:
schema: agentic-artifact/v2
id: product.rules.readme
version: 1
status: active
layer: 03.product
domain: architecture
disciplines:
- agentic
- architecture
kind: rulebook-readme
purpose: Define the product corpus home for product-owned structured rulebook YAML.
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
# Product Rules

This directory contains structured product rules for apps, packages/core,
design-system, frontend-kit, platform, and product-wide concerns.

Use owner topic subdirectories for topic-specific rules:

- `apps/` for app and product composition rules.
- `core/` for packages/core contract rules.
- `design-system/` for design-system and design-label rules.
- `frontend-kit/` for reusable frontend-kit rules.
- `platform/` for platform runtime, adapters, and product platform concerns.
- `concerns/` for product-wide concerns that intentionally span product
  subcorpora.

Cross-corpus shared rules, deploy-only rules, and harness-only rules do not
belong here unless a governed split assigns the product-owned piece to this
corpus.
