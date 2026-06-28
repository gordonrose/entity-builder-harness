<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.skills.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
kind: skill-index
purpose: List reusable RAG/rulebook model procedures.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.workflows.default
  path: .agentic/02.rag-rulebook/workflows/default.md
-->
# RAG/Rulebook Skills

- `ab-context-evaluation.md` - compare a RAG-derived context packet with
  direct source verification for planning, discovery, and investigation
  requests.
