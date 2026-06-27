<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: layer-readme
purpose: Define the RAG and rulebook layer boundary for standalone corpus, retrieval, and context-packet work.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: repo.agents
  path: AGENTS.md
- id: shared.routing-policy
  path: .agentic/routing-policy.yaml
-->
# 02.rag-rulebook Layer

## Purpose

Own reusable RAG and rulebook machinery.

This layer covers turning source material into structured rulebooks, defining
intent and context-packet schemas, building indexes and graph relationships,
chunking rulebook artifacts, and designing standalone retrieval services that
can serve multiple domain corpora.

## Boundary

This layer owns the reusable rulebook/RAG system, not every domain corpus.

Domain corpus IDs should align with the numbered layer system:

- `corpus.00.chat` for chat lifecycle and git governance
- `corpus.01.harness` for agentic harness work
- `corpus.02.rag-rulebook` for the RAG/rulebook service itself
- `corpus.03.product` for product, platform, apps, and design-system work
- `corpus.04.deploy` for infrastructure, release, and runtime operations
- `corpus.05.education` for teaching and publishing work
- `corpus.06.shared` for cross-layer process primitives

The RAG/rulebook service may index those corpora, but it should not merge them
into one undifferentiated instruction set.

Subcorpora may be introduced when a layer needs more precision, such as
`corpus.03.product.apps`, `corpus.03.product.design-system`, or
`corpus.03.product.platform`.

## Source Of Truth

- Layer workflows: `.agentic/02.rag-rulebook/workflows/`
- Layer standards: `.agentic/02.rag-rulebook/standards/`
- Layer guides: `.agentic/02.rag-rulebook/guides/`
- Layer schemas: `.agentic/02.rag-rulebook/schemas/`
- Layer policies: `.agentic/02.rag-rulebook/policies/`
- Layer derivation reports: `.agentic/02.rag-rulebook/derivation-reports/`
- Layer retirement records: `.agentic/02.rag-rulebook/retirements/`
- Layer corpus gaps: `.agentic/02.rag-rulebook/corpus-gaps/`
- Layer plans: `.agentic/02.rag-rulebook/plans/`
- Layer source material: `docs/02.rag-rulebook/source-material/`
- Layer structured rulebook content: `docs/02.rag-rulebook/rules/`
- Layer command surface: `scripts/02.rag-rulebook/`
- Current prototype rulebook artifacts: `docs/harness/architecture/`

The current architecture YAMLs under `docs/harness/architecture/` are treated
as a prototype corpus until a governed migration gives domain rulebooks their
final homes.

## Workflows

- `workflows/default.md` - plan or change RAG/rulebook schemas, corpora,
  indexes, graph retrieval, context packets, or standalone service boundaries.
- `workflows/derive-rules-from-source.md` - convert approved source material
  into structured rulebook proposals with drift and conflict review.
- `workflows/review-recognition-candidates.md` - review unmatched or ambiguous
  prompt terms before changing curated recognition sources.

## Standards

- `standards/portable-service-contract.md` - defines the reusable service
  boundary for corpus, index, chunk, intent, retrieval, and context-packet work.
- `standards/domain-corpus-package.md` - defines the modular corpus package
  shape for numbered corpora and subcorpora.
- `standards/retrieval-selector-policy-system.md` - defines the evolvable,
  multi-dimensional policy system for selecting small, accurate, validated
  context packets.
- `standards/recognition-source-system.md` - defines governed lookup sources
  used to recognize prompt intent before retrieval selection.
- `standards/recognition-candidate-review.md` - defines how important
  unmatched terms become reviewable candidates before curated-source changes.
- `standards/retrieval-selector-evaluations.md` - defines evaluation fixture
  rules for retrieval selector and context-packet behavior.
- `standards/source-to-rule-derivation.md` - defines how approved source
  material becomes structured rules while preserving drift and conflict review.

## Schemas

- `schemas/context-packet.schema.yml` - defines the v1 context-packet contract
  returned by the portable RAG/rulebook service.
- `schemas/rulebook-index.schema.yml` - defines the v1 rulebook index
  contract for current prototype paths, proposed corpus paths, artifacts,
  rules, rule packs, chunk candidates, graph edges, references, diagnostics,
  and provenance.
- `schemas/retrieval-policy-pack.schema.yml` - defines the v1 policy-pack
  contract used by retrieval selectors.
- `schemas/retrieval-policy-dimension.schema.yml` - defines the v1 imported
  dimension contract for policy-pack dimensions.
- `schemas/recognition-source.schema.yml` - defines the v1 lookup-source
  contract for generated and curated prompt recognition vocabularies.
- `schemas/recognition-candidate.schema.yml` - defines the v1 review record
  for important unmatched or ambiguous prompt terms.
- `schemas/source-to-rule-derivation-report.schema.yml` - defines the v1
  report contract for source-to-rule derivation and semantic drift review.
- `schemas/retirement-record.schema.yml` - defines the v1 record contract for
  retired, renamed, superseded, or retained-retired RAG/rulebook artifacts.
- `recognition-sources/generated/artifacts.yml` - generated lookup source for
  exact artifact IDs, paths, schemas, rule IDs, and rule-pack IDs.
- `recognition-sources/generated/routing.yml` - generated lookup source for
  governed layer, mode, corpus, and workflow routing terms.
- `recognition-sources/curated/aliases.yml` - reviewed human-language aliases
  that map to governed routing terms without replacing session metadata.
- `recognition-sources/curated/actions.yml` - reviewed action vocabulary used
  to understand requested operations.
- `recognition-sources/curated/intent-forms.yml` - reviewed question and
  command forms used to distinguish planning, explanation, implementation, git
  execution, and deploy execution requests.
- `recognition-sources/curated/risks.yml` - reviewed risk, stop-condition,
  and check vocabulary used to raise validation scrutiny.
- `recognition-candidates/` - durable review inbox for candidate terms that may
  later update curated sources.
- `corpus-gaps/` - durable records for known missing corpus coverage, including
  gaps that local context queries should surface before a domain corpus is
  ready.
- `derivation-reports/` - durable reports for source-material changes that
  affect structured rulebook content, drift, conflict review, indexes, chunks,
  or selector evaluations.
- `retirements/` - durable records for retired source material, rules, rule
  packs, derivation reports, corpus gaps, recognition sources, evaluations,
  generated indexes, chunks, runtime caches, workflows, and scripts.
- `docs/02.rag-rulebook/source-material/mcp-server-deployment-architecture.md`
  - first source coverage for the MCP server recognition candidate, before
  structured rulebook conversion.
- `docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml`
  - structured rulebook coverage for MCP server deployment architecture,
  before generated chunks and selector evaluation proof.
- `scripts/02.rag-rulebook/validate-recognition-candidates/script.sh` -
  validates recognition-candidate YAML files for sentence context, proposed
  canonical meaning, review state, duplicate IDs, and accepted-candidate proof.
- `scripts/02.rag-rulebook/report-recognition-candidates/script.sh` - reports
  recognition-candidate review state, coverage state, and allowed next actions
  without mutating curated sources.
- `scripts/02.rag-rulebook/build-local-runtime/script.sh` - builds an ignored
  local runtime cache with generated index, chunks, manifest, and validation
  report, plus fingerprints for live selector inputs.
- `scripts/02.rag-rulebook/check-runtime-freshness/script.sh` - verifies that
  a built local runtime cache still matches current governed input and
  runtime-output fingerprints.
- `scripts/02.rag-rulebook/check-corpus-root-changes/script.sh` - detects
  changed governed corpus-root files and requires retirement, coverage,
  indexing, or chunking proof depending on the change type.
- `scripts/02.rag-rulebook/query-local-context/script.sh` - reads a local
  runtime cache and emits a validated context packet for request text plus
  session metadata, refusing stale runtime caches.
- `scripts/02.rag-rulebook/generate-recognition-sources/script.sh` -
  generates and checks metadata-backed recognition sources.
- `scripts/02.rag-rulebook/validate-recognition-sources/script.sh` -
  validates recognition-source YAML files for shape, provenance, duplicates,
  refresh policy, and curated-source review rules.

## Policies

- `policies/retrieval-selector/v1.yml` - seed v1 policy-pack manifest for
  prompt, session metadata, layer/mode/workflow, paths, corpus ownership, graph
  expansion, checks, stops, token budgets, confidence, validation handoff, and
  future semantic recall.
- `policies/retrieval-selector/v1/dimensions/` - imported per-dimension policy
  contracts used by the seed v1 policy pack.
  The prompt dimension now names recognition sources and extraction rules for
  turning raw user language into structured retrieval signals.
- `evaluations/retrieval-selector/v1/fixtures/` - active selector evaluation
  fixtures with expected and banned context-packet outcomes.

## Guides

- `guides/context-packet.md` - teaches the context-packet mental model, field
  families, good and bad packet shapes, and how an LLM should use the packet.
- `guides/rulebook-index.md` - teaches the rulebook index mental model, field
  families, migration safety role, graph relationships, and future validator
  expectations.
- `guides/retrieval-policy-dimension.md` - teaches how to read and author
  imported retrieval policy dimensions.
- `guides/retirement-record.md` - teaches how retirement records keep removed
  or superseded RAG artifacts auditable.

## Source Material

- `docs/02.rag-rulebook/source-material/` - early source coverage for concepts
  that are not yet structured rulebook YAML, indexed chunks, or selector
  evaluation fixtures.

## Structured Rulebook Content

- `docs/02.rag-rulebook/rules/` - governed YAML rulebook content converted
  from source material before indexing, chunking, and selector evaluation.

## Plans

- `plans/repo-plan.md` - records the ordered plan for turning the prototype
  rulebook into modular RAG-ready corpora and service inputs.
- `plans/prototype-corpus-migration-map.yml` - inventories the current
  prototype corpus and maps YAML rules, rule packs, source guides, and ADRs to
  proposed numbered corpus packages before any file moves.

## Commands

- `scripts/02.rag-rulebook/generate-rulebook-index/script.sh` - emits a
  read-only `rag-rulebook/rulebook-index/v1` JSON index from the current
  prototype architecture rulebook, numbered corpus rule roots such as
  `docs/02.rag-rulebook/rules/` and `docs/04.deploy/rules/`, and migration
  map.
- `scripts/02.rag-rulebook/validate-rulebook-index/script.sh` - validates a
  `rag-rulebook/rulebook-index/v1` JSON index without modifying files.
- `scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh` - emits
  read-only `rag-rulebook/chunk-set/v1` JSON chunks from a validated rulebook
  index.
- `scripts/02.rag-rulebook/validate-context-packet/script.sh` - validates a
  `rag-rulebook/context-packet/v1` JSON packet against generated
  `rag-rulebook/chunk-set/v1` chunks without modifying files.
- `scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh` - emits
  a small validated `rag-rulebook/context-packet/v1` fixture from generated or
  saved chunks without modifying files.
- `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh` -
  emits the first deterministic selector fixture by combining the active policy
  pack, recognition-source matches, recognition-candidate coverage gaps,
  session-like metadata, focused paths, and generated or saved chunks before
  validating the packet.
- `scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh` -
  runs retrieval selector evaluation fixtures against generated selector
  packets.
- `scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh` -
  validates a `rag-rulebook/retrieval-policy-pack/v1` YAML policy pack without
  modifying files.
- `scripts/02.rag-rulebook/validate-recognition-candidates/script.sh` -
  validates `rag-rulebook/recognition-candidate/v1` YAML review records
  without modifying files.
- `scripts/02.rag-rulebook/validate-derivation-reports/script.sh` - validates
  `rag-rulebook/source-to-rule-derivation-report/v1` YAML reports without
  modifying files.
- `scripts/02.rag-rulebook/validate-retirement-records/script.sh` - validates
  `rag-rulebook/retirement-record/v1` YAML records without deleting files or
  rewriting references.

## Output Locations

Do not create a RAG server, MCP server, or new domain corpus without explicit
task scope.

When durable output locations are introduced, prefer modular corpus roots over
placing product, design-system, deploy, and harness rules together under one
harness-owned docs tree.
