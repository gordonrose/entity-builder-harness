<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.workflows.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: governance
disciplines:
- agentic
kind: workflow-index
purpose: List workflows for RAG and rulebook layer work.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: shared.routing-policy
  path: .agentic/routing-policy.yaml
-->
# RAG/Rulebook Workflows

- `default.md` - govern changes to standalone RAG/rulebook service design,
  intent and context-packet schemas, rulebook corpus generation, indexing,
  chunking, graph retrieval, and domain corpus boundaries.
