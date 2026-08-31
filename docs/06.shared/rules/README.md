<!-- agentic-artifact:
schema: agentic-artifact/v2
id: shared.rules.readme
version: 1
status: active
layer: 06.shared
domain: governance
disciplines:
- agentic
- architecture
kind: rulebook-readme
purpose: Define the shared corpus home for deliberately cross-layer structured rulebook YAML.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: shared.corpus.readme
  path: docs/06.shared/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Shared Rules

This directory contains structured rules for requirements that deliberately
span multiple numbered layers and cannot honestly be owned by one narrower
corpus.

Use `concerns/` for cross-layer concern rules such as dependency direction,
generated-code policy, CI quality, and TypeScript monorepo tooling.

Prefer a narrower owner corpus when one layer can make, validate, and maintain
the rule. Shared placement is for rules whose authority must stay cross-layer.
