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
- `validate-rulebook-index/script.sh` validates a
  `rag-rulebook/rulebook-index/v1` JSON index for duplicate IDs, broken
  references, count drift, graph-edge resolution, path existence, and
  diagnostics consistency.
- `generate-rulebook-chunks/script.sh` emits read-only
  `rag-rulebook/chunk-set/v1` JSON chunks from a validated rulebook index.
- `validate-context-packet/script.sh` validates a
  `rag-rulebook/context-packet/v1` JSON packet against a generated
  `rag-rulebook/chunk-set/v1` JSON chunk set.
- `generate-context-packet-fixture/script.sh` emits a small validated
  `rag-rulebook/context-packet/v1` fixture from generated or saved chunks.
- `validate-retrieval-policy-pack/script.sh` validates a
  `rag-rulebook/retrieval-policy-pack/v1` YAML policy pack before selector
  runtime code can rely on it.

Do not add new implementation scripts here until a governed task defines the
capability boundary, inputs, effects, and validation.
