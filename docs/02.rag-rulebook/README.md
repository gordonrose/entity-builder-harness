<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.corpus.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: corpus
disciplines:
- agentic
- architecture
kind: corpus-readme
purpose: Define the RAG-readable RAG/rulebook corpus boundary for source material, rules, ADRs, and retrieval knowledge.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.standard.domain-corpus-package
  path: .agentic/02.rag-rulebook/standards/domain-corpus-package.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 02.rag-rulebook Corpus

This directory is the RAG-readable corpus package for RAG/rulebook knowledge.

The governing workflows, policies, schemas, validators, and service machinery
for RAG/rulebook behavior live under `.agentic/02.rag-rulebook/`. This
directory contains human-readable source material, ADR history, structured
rules, and related corpus files that the RAG/rulebook service can index,
chunk, cite, and evaluate.

Use this corpus for RAG/rulebook source material, retrieval decisions,
context-packet decisions, source-to-rule guidance, structured RAG/rulebook
rules, and corpus-package documentation.

Do not store product runtime contracts, deployment operations, or generic
harness governance here unless the material is specifically about how the
RAG/rulebook layer retrieves, indexes, chunks, validates, or serves context.

During the prototype corpus migration, older RAG/rulebook-oriented material
may remain under `docs/harness/architecture/**` until a governed artifact path
migration moves it and leaves pointer compatibility.
