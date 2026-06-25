<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.scripts.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: scripts
disciplines:
- agentic
kind: script-layer-readme
purpose: Reserve the RAG and rulebook executable command surface for future standalone retrieval and corpus tooling.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: chat.script-layout
  path: docs/00.chat/script-layout.md
-->
# 02.rag-rulebook Scripts

This directory is reserved for future RAG/rulebook command capabilities such as
corpus extraction, rulebook index generation, chunk generation, graph expansion,
context-packet validation, and standalone service adapters.

Do not add implementation scripts here until a governed task defines the
capability boundary, inputs, effects, and validation.
