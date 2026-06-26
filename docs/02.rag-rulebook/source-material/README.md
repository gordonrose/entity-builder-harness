<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-material.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: source-material-readme
purpose: Define the RAG/rulebook source-material holding area before material is converted into structured rulebook artifacts.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.schema.recognition-candidate
  path: .agentic/02.rag-rulebook/schemas/recognition-candidate.schema.yml
-->
# Source Material

This directory holds early source material before it becomes structured
rulebook YAML, generated chunks, and selector evaluation coverage.

Source material lives under `docs/02.rag-rulebook/` because it is corpus
content. The governing schemas, workflows, policies, and validators stay under
`.agentic/02.rag-rulebook/`.

Source material can move a recognition candidate from `coverage.status:
missing` to `coverage.status: partial`, but it is not enough to mark the
candidate as fully covered.

Use this directory for small, reviewed notes that define a concept, boundary,
risk, or architecture question clearly enough for later rulebook conversion.
