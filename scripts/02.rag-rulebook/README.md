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
  architecture rulebook, numbered corpus rule roots such as
  `docs/02.rag-rulebook/rules/` and `docs/04.deploy/rules/`, and migration
  map.
- `validate-rulebook-index/script.sh` validates a
  `rag-rulebook/rulebook-index/v1` JSON index for duplicate IDs, broken
  references, count drift, graph-edge resolution, path existence, and
  diagnostics consistency.
- `generate-rulebook-chunks/script.sh` emits read-only
  `rag-rulebook/chunk-set/v1` JSON chunks from a validated rulebook index.
- `build-local-runtime/script.sh` writes a local deterministic runtime cache
  containing the generated rulebook index, chunk set, manifest, and validation
  report.
- `query-local-context/script.sh` reads a built local runtime cache and emits a
  validated `rag-rulebook/context-packet/v1` packet for request text plus
  session metadata.
- `validate-context-packet/script.sh` validates a
  `rag-rulebook/context-packet/v1` JSON packet against a generated
  `rag-rulebook/chunk-set/v1` JSON chunk set.
- `generate-context-packet-fixture/script.sh` emits a small validated
  `rag-rulebook/context-packet/v1` fixture from generated or saved chunks.
- `generate-retrieval-selector-fixture/script.sh` emits a validated
  `rag-rulebook/context-packet/v1` selector fixture from the active policy
  pack, recognition-source matches, recognition-candidate coverage gaps,
  session-like metadata, focused paths, and generated or saved chunks.
- `evaluate-retrieval-selector-fixtures/script.sh` runs machine-readable
  retrieval selector evaluation fixtures against generated selector packets.
- `generate-recognition-sources/script.sh` emits or checks generated
  `rag-rulebook/recognition-source/v1` YAML lookup sources derived from the
  artifact metadata index and governed routing, layer, corpus, mode, and
  workflow sources.
- `validate-retrieval-policy-pack/script.sh` validates a
  `rag-rulebook/retrieval-policy-pack/v1` YAML policy pack before selector
  runtime code can rely on it.
- `validate-yaml-syntax/script.sh` parses governed RAG/rulebook and deploy
  YAML files before narrower validators run.
- `validate-recognition-sources/script.sh` validates
  `rag-rulebook/recognition-source/v1` YAML lookup sources before generated or
  curated prompt-recognition vocabulary can be committed.
- `validate-recognition-candidates/script.sh` validates
  `rag-rulebook/recognition-candidate/v1` YAML review records before prompt
  vocabulary candidates can be committed or reviewed.
- `validate-derivation-reports/script.sh` validates
  `rag-rulebook/source-to-rule-derivation-report/v1` YAML reports before
  source-derived rules, chunks, or selector expectations are treated as
  current.
- `report-recognition-candidates/script.sh` validates recognition candidates
  and reports review state, coverage state, and allowed next actions without
  mutating curated sources.
- `commit-gates/script.sh` runs the RAG/rulebook validators that must pass
  before a chat task commit when `.agentic/02.rag-rulebook` exists.

Do not add new implementation scripts here until a governed task defines the
capability boundary, inputs, effects, and validation.
