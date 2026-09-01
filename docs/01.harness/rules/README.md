<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.rules.readme
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: rulebook-readme
purpose: Define the harness corpus home for harness-owned structured rulebook YAML.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.corpus.readme
  path: docs/01.harness/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# Harness Rules

This directory contains structured harness rules for governance, repository
automation boundaries, metadata, migration helpers, and command-surface
behavior owned by `corpus.01.harness`.

Use `layers/` for harness-owned repo layer rules. Put cross-layer concerns in
`docs/06.shared/rules/` unless the harness layer is the only honest owner.

Harness rules are RAG-readable governance content. They do not replace the
executable workflows, gates, standards, or scripts under `.agentic/01.harness/`
and `scripts/01.harness/`.
