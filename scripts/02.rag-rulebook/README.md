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
purpose: Define the RAG and rulebook executable command surface for standalone retrieval and corpus tooling.
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

This directory owns RAG/rulebook command capabilities such as corpus extraction,
rulebook index generation, chunk generation, graph expansion, context-packet
validation, and standalone service adapters.

## Commands

- `generate-rulebook-index/script.sh` emits a read-only
  `rag-rulebook/rulebook-index/v1` JSON index for the current prototype
  architecture rulebook and migration map.

Do not add new implementation scripts here until a governed task defines the
capability boundary, inputs, effects, and validation.
