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
- `review-okf-source-material.md` - govern iterative architect, agentic
  engineer, and senior SRE review of OKF source material before it can be
  treated as approved input for derivation.
- `derive-rules-from-source.md` - govern approved source-material conversion
  into structured rules, with required drift and conflict review.
- `review-recognition-candidates.md` - govern review of unmatched, ambiguous,
  or corrected prompt terms before curated recognition sources are changed.

## Related Skills

- `../skills/ab-context-evaluation.md` - use for RAG-versus-source A/B
  comparison when answering planning, discovery, or investigation prompts.
