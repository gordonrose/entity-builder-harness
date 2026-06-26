<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.rules.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: rulebook-readme
purpose: Define where structured RAG/rulebook corpus rules live after source material has been reviewed.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Rulebook Rules

This directory holds structured RAG/rulebook corpus rules.

Use `source-material/` for early notes and unresolved architecture questions.
Use `rules/` after the source material has been converted into governed YAML
that can later be indexed, chunked, evaluated, and served by the portable
RAG/rulebook service.

Structured rulebook YAML is still corpus content. The policies, schemas,
validators, and workflows that govern it stay under `.agentic/02.rag-rulebook/`.
