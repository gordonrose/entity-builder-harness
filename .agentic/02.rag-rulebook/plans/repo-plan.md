<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.plan.repo
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: plan
purpose: Record the ordered repo plan for turning the prototype rulebook into modular RAG-ready corpora.
portability:
  class: internal
  targets: []
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: rag-rulebook.workflows.default
  path: .agentic/02.rag-rulebook/workflows/default.md
-->
# RAG/Rulebook Repo Plan

## Goal

Create a portable RAG/rulebook service model that can support multiple modular
domain corpora without folding product, design-system, deployment, education,
and harness instructions into one harness-owned corpus.

Corpus IDs should align with the numbered layer system, including
`corpus.02.rag-rulebook` as the self-corpus for the service's own governance.

## Current State

The repo has a first-class `02.rag-rulebook` layer and a prototype architecture
rulebook under `docs/harness/architecture/`.

The prototype rulebook proves useful structure:

- source guides
- YAML layer rulesets
- YAML concern rulesets
- YAML task rule packs
- source references
- metadata headers

The location is not the final domain corpus model.

## Ordered Plan

1. Define the portable service contract.
   - Status: present in `standards/portable-service-contract.md`.

2. Define the domain corpus package shape.
   - Status: present in `standards/domain-corpus-package.md`.
   - Corpus IDs now align with numbered layers.

3. Design a context-packet schema.
   - Include intent, routing metadata, matched corpora, selected chunks,
     required checks, stop conditions, citations, confidence, and gaps.
   - Status: present in `schemas/context-packet.schema.yml`.

3a. Inventory the prototype corpus and migration targets.
   - Map current `docs/harness/architecture/` source guides, ADRs, YAML layer
     rulesets, concern rulesets, and rule packs to proposed numbered corpus
     packages.
   - Do not move files in this step.
   - Status: present in `plans/prototype-corpus-migration-map.yml`.

4. Design a rulebook index schema.
   - Include corpus IDs, artifact IDs, rule IDs, chunk IDs, path globs,
     source refs, required rulesets, related rulesets, and graph edges.
   - Support both current prototype paths and proposed corpus package paths.
   - Status: present in `schemas/rulebook-index.schema.yml`.

5. Add a read-only index generator.
   - Parse the current prototype YAML rulebook.
   - Emit deterministic JSON.
   - Validate duplicate IDs and missing references.
   - Do not use embeddings or network calls.
   - Status: present in
     `scripts/02.rag-rulebook/generate-rulebook-index/script.sh`.

5a. Add a read-only rulebook index validator.
   - Validate shape, duplicate IDs, references, graph edges, path mappings,
     diagnostics, and source path existence.
   - Fail when the generated index is internally inconsistent or hides
     blocking unresolved references.
   - Status: present in
     `scripts/02.rag-rulebook/validate-rulebook-index/script.sh`.

6. Add a chunk generator.
   - Chunk by YAML structure, not arbitrary character windows.
   - Preserve parent artifact IDs, rule IDs, paths, source refs, and severity.
   - Status: present in
     `scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh`.

7. Add context-packet validation.
   - Validate packet shape and references.
   - Report gaps when retrieval is ambiguous or insufficient.
   - Status: present in
     `scripts/02.rag-rulebook/validate-context-packet/script.sh`.

7a. Add a deterministic context-packet fixture builder.
   - Assemble a small packet from generated chunks.
   - Validate the packet before output.
   - Keep this as a fixture, not semantic retrieval.
   - Status: present in
     `scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh`.

7b. Define the retrieval selector policy system.
   - Make retrieval behavior policy-driven, not hard-coded.
   - Cover prompt, session metadata, layer/mode/workflow, focused paths,
     corpus ownership, graph expansion, required checks, stop conditions,
     token budget, confidence thresholds, validation handoff, and future
     semantic recall.
   - Add a policy-pack schema and seed v1 policy pack.
   - Status: present in
     `standards/retrieval-selector-policy-system.md`,
     `schemas/retrieval-policy-pack.schema.yml`, and
     `policies/retrieval-selector/v1.yml`.

7c. Add a read-only retrieval policy-pack validator.
   - Validate policy-pack shape, dimensions, precedence, thresholds,
     referenced validators, smoke fixtures, and v1 semantic-recall safety.
   - Status: present in
     `scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh`.

7d. Modularize retrieval policy dimensions.
   - Keep `policies/retrieval-selector/v1.yml` as the active policy-pack
     manifest.
   - Move each dimension into an imported file with required inputs, expected
     actions, banned actions, output obligations, gaps/stops, ranking effects,
     validation examples, and allowed change paths.
   - Validate all imports before selector runtime code can depend on them.
   - Status: present in `schemas/retrieval-policy-dimension.schema.yml` and
     `policies/retrieval-selector/v1/dimensions/`.

7e. Define recognition-source architecture.
   - Separate recognition lookup sources from retrieval chunks.
   - Govern generated sources such as artifact IDs, paths, schemas, corpora,
     layers, workflows, rules, and rule packs.
   - Govern curated sources such as action verbs, risk words, domain nouns,
     aliases, stop-condition words, and check names.
   - Keep prompt-time lookup fast by using prebuilt or compiled sources rather
     than rebuilding inventories on every prompt.
   - Status: present in `standards/recognition-source-system.md`,
     `schemas/recognition-source.schema.yml`, and the prompt dimension policy.

7f. Add recognition-source validation.
   - Validate recognition-source YAML before generated or curated lookup
     sources become commit-critical.
   - Reject stale generated terms without evidence paths, duplicate lookup
     terms, missing source artifacts, missing generation commands, and curated
     terms without review triggers.
   - Status: present in
     `scripts/02.rag-rulebook/validate-recognition-sources/`.

8. Plan the prototype corpus migration.
   - Separate harness-owned rules from `corpus.03.product`,
     `corpus.03.product.design-system`, `corpus.04.deploy`, and
     `corpus.05.education`.
   - Include `corpus.02.rag-rulebook` as a self-corpus for service governance.
   - Use artifact path migration before moving committed files.

9. Only after the above, design a standalone service or repo extraction.
   - The service should consume corpus packages and generated indexes.
   - The workbench should call the service; it should not own the service.

## Non-Goals For The Current Stage

- Do not build the RAG server.
- Do not build an MCP server.
- Do not move `docs/harness/architecture/` files.
- Do not introduce embeddings before deterministic indexes and chunks exist.
- Do not merge domain corpora into one instruction set.

## Next Small Slice

Add the first read-only retrieval selector fixture that consumes the validated
compiled policy pack, generated chunks, recognition-source signals, request
text, and session-like metadata before emitting a validated context packet.
