<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.corpus.readme
version: 1
status: active
layer: 01.harness
domain: governance
disciplines:
- agentic
- architecture
kind: corpus-readme
purpose: Define the RAG-readable harness corpus boundary for harness decisions, source material, rules, and migration history.
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
# 01.harness Corpus

This directory is the RAG-readable harness corpus package for
`corpus.01.harness`.

The governing workflows, standards, checklists, agents, gates, and templates
for harness behavior live under `.agentic/01.harness/`. This directory contains
human-readable corpus material that the RAG/rulebook service can index, chunk,
cite, and evaluate.

Use this corpus for harness ADRs, harness source material, harness-owned
structured rules, command-surface rules, metadata migration history, and
documentation layout decisions.

Harness ADRs live under `adrs/`.

Do not store product runtime contracts, deployment runbooks, reusable
RAG/rulebook service rules, or general shared-process standards here unless the
decision owner is the harness layer.

During the prototype corpus migration, old harness-oriented material remains
under `docs/harness/architecture/**` until a governed artifact path migration
moves a concrete source and target pair.
