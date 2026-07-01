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
- `compile-retrieval-policy/script.sh` emits
  `rag-rulebook/compiled-retrieval-policy/v1` JSON from validated retrieval
  policy, imported dimensions, recognition sources, corpus ownership, and rule
  graph metadata.
- `build-local-runtime/script.sh` writes a local deterministic runtime cache
  containing the generated rulebook index, chunk set, manifest, and validation
  report, plus compiled retrieval policy and fingerprints for live selector
  inputs.
- `check-runtime-freshness/script.sh` verifies that a built local runtime cache
  still matches current governed input and runtime-output fingerprints.
- `check-source-projections/script.sh` verifies that governed source material
  is declared in the active projection manifest, derived YAML projections
  exist, carry current source hashes, have derivation reports, and retain
  expected selector or corpus-gap proof paths.
- `generate-derived-rules/script.sh` emits a read-only source-to-rule
  projection plan from the active manifest, including current source hashes,
  derivation report status, existing YAML provenance state, and the actions a
  future apply step would need. With explicit `--apply-provenance`, it rewrites
  only existing top-level `source_derivation` blocks for declared rule paths.
- `generate-source-to-rule-work-order/script.sh` emits a read-only work order
  for semantic source-to-rule derivation, including source outlines, hashes,
  expected YAML projections, derivation report state, selector proof paths,
  corpus gaps, required checks, and ordered next actions.
- `generate-source-to-rule-draft-packet/script.sh` emits a read-only semantic
  draft packet that includes bounded source, current YAML, derivation report,
  corpus-gap, and selector-evaluation content for an agent or reviewer to
  propose source-derived YAML changes without rediscovering context.
- `check-source-material-coverage/script.sh` verifies that governed source
  material has a structured rule, derivation report, or corpus gap outcome and
  that claimed structured rules reached the generated index and chunk set.
- `check-corpus-root-changes/script.sh` detects changed governed corpus-root
  files, requires retirement records for deleted or renamed old paths, and
  proves changed rule files still reach generated index and chunks.
- `query-local-context/script.sh` reads a built local runtime cache and emits a
  validated `rag-rulebook/context-packet/v1` packet, or a compact derived
  `rag-rulebook/context-packet-compact/v1` view, for request text plus request
  context and session safety metadata, refusing stale runtime caches and
  including selector trace diagnostics.
- `run-local-service/script.sh` starts the thin local HTTP service for the MSP
  API surface: `GET /health`, `GET /version`, and `POST /context/query`.
- `build-service-image/script.sh` builds the governed local container image for
  the existing RAG/rulebook HTTP service from
  `infra/04.deploy/02.rag-rulebook/image/Dockerfile`; it does not publish,
  deploy, call AWS, or mutate GitHub.
- `smoke-test-service-image/script.sh` builds and runs that image locally,
  mounts a freshly built runtime cache read-only, and verifies health, version,
  token enforcement, and compact context-query behavior.
- `validate-context-packet/script.sh` validates a
  `rag-rulebook/context-packet/v1` JSON packet against a generated
  `rag-rulebook/chunk-set/v1` JSON chunk set.
- `validate-okf-source-material-reviews/script.sh` validates accepted OKF
  source-material review records, including current source hashes, required
  reviewer roles, reviewer scores above threshold, final blocker state, and
  final decision consistency.
- `generate-context-packet-fixture/script.sh` emits a small validated
  `rag-rulebook/context-packet/v1` fixture from generated or saved chunks.
- `generate-retrieval-selector-fixture/script.sh` emits a validated
  `rag-rulebook/context-packet/v1` selector fixture from the active policy
  pack, recognition-source matches, recognition-candidate coverage gaps,
  session-like metadata, focused paths, generated or saved chunks, and compiled
  retrieval strategy.
- `evaluate-retrieval-selector-fixtures/script.sh` runs machine-readable
  retrieval selector evaluation fixtures against generated selector packets,
  including selector trace assertions when fixtures require them.
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
- `validate-retirement-records/script.sh` validates
  `rag-rulebook/retirement-record/v1` YAML records before removed, renamed,
  superseded, or retained-retired RAG artifacts are treated as governed.
- `report-recognition-candidates/script.sh` validates recognition candidates
  and reports review state, coverage state, and allowed next actions without
  mutating curated sources.
- `commit-gates/script.sh` runs the RAG/rulebook validators that must pass
  before a chat task commit when `.agentic/02.rag-rulebook` exists.

Do not add new implementation scripts here until a governed task defines the
capability boundary, inputs, effects, and validation.
