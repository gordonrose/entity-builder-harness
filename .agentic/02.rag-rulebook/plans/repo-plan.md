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

Create a portable Operational Knowledge Framework with a RAG/rulebook delivery
model that can support multiple modular domain corpora without folding product,
design-system, deployment, education, and harness instructions into one
harness-owned corpus.

The OKF is the governed knowledge system: source material, rules, rule packs,
policies, provenance, reviews, evaluations, checks, stop conditions, and
corpus packages. RAG is one delivery/runtime interface over that governed
knowledge, serving small validated context packets to agents.

Corpus IDs should align with the numbered layer system, including
`corpus.02.rag-rulebook` as the self-corpus for the service's own governance.

The long-term product direction is a provider-agnostic governed context service
for coding agents. An engineer should be able to create an account, install a
small local bootstrap/client, add minimal `AGENTS.md` or `CLAUDE.md`
instructions, configure credentials outside the repo, and retrieve small,
validated, repo-aware best-practice context packets from a remote service.

In that model, local `.agentic` harness material becomes the development and
fallback implementation. Over time, most heavy rulebook, retrieval, evaluation,
and policy machinery can move behind a hosted API or MCP service. Local repos
should retain only a small auditable bootstrap, service URL/config discovery,
credential instructions, safe stop conditions, and last-known-good fallback
behavior.

## Current State

The repo has a first-class `02.rag-rulebook` layer and a prototype architecture
rulebook under `docs/harness/architecture/`.

The deterministic foundation is now strong enough to bootstrap local RAG before
deployment. Local RAG should come before deploy-corpus expansion so agents can
use validated local context packets while the deploy corpus is being built.

The local runtime path is executable: `build-local-runtime` writes a local
deterministic cache, `check-runtime-freshness` verifies that cache against live
inputs, and `query-local-context` returns validated context packets from the
cache. The runtime now includes a compiled retrieval policy artifact so selector
behavior is loaded from governed policy inputs rather than hidden selector
constants. Context packets now include a compact selector trace so retrieval
misses can be diagnosed by stage instead of treated as isolated prompt gaps.
This local runtime is the proof target before a hosted API or MCP surface is
treated as shippable.

The prototype rulebook proves useful structure:

- source guides
- YAML layer rulesets
- YAML concern rulesets
- YAML task rule packs
- source references
- metadata headers

The location is not the final domain corpus model.

Production-grade source material now needs an OKF quality review loop before
source-to-rule derivation. That loop requires architect, agentic engineer,
SecOps engineer, and senior SRE review, and every reviewer must score the
source material above 9.5/10 with no blocking gaps remaining before structured
YAML, chunks, selector evaluations, or deploy guidance are treated as current.

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

7g. Generate the first metadata-backed recognition source.
   - Generate `recognition.generated.artifacts` from the artifact metadata
     index instead of parsing headers separately.
   - Commit the generated source at
     `.agentic/02.rag-rulebook/recognition-sources/generated/artifacts.yml`.
   - Check generated-source freshness at the RAG/rulebook commit boundary.
   - Status: present in
     `scripts/02.rag-rulebook/generate-recognition-sources/` and
     `recognition-sources/generated/artifacts.yml`.

7h. Generate the routing recognition source.
   - Generate `recognition.generated.routing` from governed layer taxonomy,
     routing policy, retrieval policy, corpus IDs, modes, and workflow files.
   - Commit the generated source at
     `.agentic/02.rag-rulebook/recognition-sources/generated/routing.yml`.
   - Keep the same generator, validator, and commit-gate freshness check as
     the artifact recognition source.
   - Status: present in
     `scripts/02.rag-rulebook/generate-recognition-sources/` and
     `recognition-sources/generated/routing.yml`.

7i. Add a read-only retrieval selector fixture.
   - Consume the validated policy pack, generated chunks, recognition-source
     matches, request text, session-like metadata, and focused paths.
   - Emit a validated `rag-rulebook/context-packet/v1` packet.
   - Keep this as deterministic fixture behavior, not a production retrieval
     runtime or semantic recall engine.
   - Status: present in
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/`.

7j. Define evaluation fixture governance.
   - Add a harness-wide standard for evaluation fixtures, expected outcomes,
     banned outcomes, validators, ownership, update triggers, and pass/fail
     governance.
   - Add a RAG/rulebook-specific standard for retrieval selector evaluations,
     including routing, corpora, recognition matches, selected chunks,
     citations, checks, gaps, stops, confidence, and token-budget assertions.
   - Status: present in `.agentic/01.harness/standards/evaluation-fixtures.md`
     and `.agentic/02.rag-rulebook/standards/retrieval-selector-evaluations.md`.

7k. Add retrieval selector evaluation fixtures.
   - Add machine-readable fixtures for exact RAG/rulebook routing,
     prompt/session conflict, vague low-confidence prompts, and corpus boundary
     protection.
   - Add a read-only evaluator command that generates selector packets and
     checks expected and banned packet behavior.
   - Run the evaluator from the RAG/rulebook commit gate.
   - Status: present in
     `.agentic/02.rag-rulebook/evaluations/retrieval-selector/v1/fixtures/`
     and `scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/`.

7l. Add curated recognition sources.
   - Add reviewed sources for aliases, action verbs, risk words, stop
     conditions, and check names.
   - Prove the observed `RAG rulebook` / `rag-rulebook` alias gap with a
     retrieval selector evaluation fixture.
   - Keep curated vocabulary lower authority than generated artifact and
     routing sources.
   - Status: present in
     `.agentic/02.rag-rulebook/recognition-sources/curated/` and covered by
     `retrieval-selector.v1.curated-prompt-vocabulary`.

7m. Add intent-form recognition and precise selector assertions.
   - Add reviewed request-form vocabulary for planning, explanation,
     implementation, git execution, and deploy execution prompts.
   - Extend selector evaluations so fixtures can require or ban exact
     recognition matches by source ID, term, category, canonical ID, match
     type, and matched input.
   - Prove `How do I update my harness so we can deploy it behind an MCP
     server?` is recognized as planning guidance, not implementation or deploy
     execution.
   - Status: present in
     `recognition-sources/curated/intent-forms.yml`,
     `retrieval-selector.v1.intent-form-planning-mcp-server`, and
     `scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/`.

7n. Add recognition candidate review workflow.
   - Define candidate records for important unmatched or ambiguous prompt
     terms, including the observed sentence for meaning.
   - Define a review workflow so candidates can be accepted, rejected, merged,
     or deferred before curated sources change.
   - Keep runtime recognition cheap; do not automatically mutate curated
     source YAML from every prompt.
   - Status: present in `schemas/recognition-candidate.schema.yml`,
     `standards/recognition-candidate-review.md`,
     `workflows/review-recognition-candidates.md`, and
     `recognition-candidates/README.md`.

7o. Add recognition candidate validation.
   - Add a read-only validator for `rag-rulebook/recognition-candidate/v1`
     records.
   - Validate required sentence context, proposed canonical meaning,
     confidence weight, workflow paths, duplicate IDs, and status/review
     decision alignment.
   - Require proof paths for accepted candidates so review records cannot claim
     acceptance without a curated-source update and evaluation fixture.
   - Run the validator from the RAG/rulebook commit gate when the candidate
     inbox exists.
   - Status: present in
     `scripts/02.rag-rulebook/validate-recognition-candidates/`.

7p. Add candidate-driven corpus gap reporting.
   - Extend recognition candidates with optional corpus coverage metadata.
   - Keep meaningful but uncovered terms pending or deferred until governed
     corpus source material exists.
   - Let selector fixtures emit `missing-corpus` gaps from coverage-missing
     candidates without treating those candidates as active curated vocabulary.
   - Prove `MCP server` remains a planning prompt signal while also surfacing
     the missing MCP-server corpus coverage.
   - Status: present in
     `recognition-candidates/deferred/2026-06-26-mcp-server.yml`,
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/`, and
     `evaluations/retrieval-selector/v1/fixtures/intent-form-planning-mcp-server.yml`.

7q. Add staged recognition-candidate coverage.
   - Treat `coverage.status` as a summary, not the proof itself.
   - Add coverage stages for source material, structured rulebook content,
     indexed chunks, and selector evaluation proof.
   - Require `missing` when no required stage is present, `partial` when some
     stages are present and some are missing, and `covered` only when all
     required stages have evidence.
   - Keep missing or partial coverage visible as selector gaps until retrieval
     is fully ready.
   - Status: present in `schemas/recognition-candidate.schema.yml`,
     `scripts/02.rag-rulebook/validate-recognition-candidates/`, and
     `recognition-candidates/deferred/2026-06-26-mcp-server.yml`.

7r. Add first MCP server source material.
   - Add source material for MCP server deployment architecture before
     structured rulebook conversion.
   - Move the MCP server candidate from `coverage.status: missing` to
     `coverage.status: partial` by marking only `source_material` as present.
   - Keep structured rulebook content, indexed chunks, and selector evaluation
     stages missing so the selector continues to report the coverage gap.
   - Status: present in
     `docs/02.rag-rulebook/source-material/mcp-server-deployment-architecture.md`
     and `recognition-candidates/deferred/2026-06-26-mcp-server.yml`.

7s. Add MCP server structured rulebook coverage.
   - Convert MCP server source material into governed YAML rulebook content.
   - Move the MCP server candidate to staged partial coverage by marking
     `source_material` and `structured_rulebook` as present.
   - Keep indexed chunks and selector evaluation stages missing so the
     selector continues to report the remaining coverage gap.
   - Status: present in
     `docs/02.rag-rulebook/rules/concerns/mcp-server-deployment-architecture.yml`
     and `recognition-candidates/deferred/2026-06-26-mcp-server.yml`.

7t. Index and chunk current RAG/rulebook rules.
   - Extend the read-only rulebook index generator to scan current
     `docs/02.rag-rulebook/rules/` YAML as `corpus.02.rag-rulebook` content.
   - Prove the MCP server rulebook YAML emits artifact-summary and rule chunks
     through the existing chunk generator.
   - Move the MCP server candidate to staged partial coverage by marking
     `indexed_chunks` as present while keeping selector evaluation missing.
   - Status: present in
     `scripts/02.rag-rulebook/generate-rulebook-index/script.sh`,
     `scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`, and
     `recognition-candidates/deferred/2026-06-26-mcp-server.yml`.

7u. Add MCP server selector evaluation proof.
   - Extend the retrieval selector fixture generator so matched recognition
     candidates can make covered evidence-path chunks eligible for selection.
   - Update the MCP server planning fixture to require covered MCP rulebook
     chunks while preserving planning route semantics and banning deploy
     execution.
   - Move the MCP server candidate to `coverage.status: covered` while keeping
     review acceptance separate.
   - Status: present in
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh`,
     `evaluations/retrieval-selector/v1/fixtures/intent-form-planning-mcp-server.yml`,
     and `recognition-candidates/deferred/2026-06-26-mcp-server.yml`.

7v. Govern recognition-candidate lifecycle review.
   - Make pending, accepted, rejected, deferred, merged, and corpus-gap
     outcomes explicit.
   - Require lifecycle directory and status alignment for durable candidate
     records.
   - Require terminal review records to include reviewer identity, reviewed
     timestamp, and reviewer notes.
   - Keep the MCP server candidate review-governed after coverage proof until
     a separate review accepts, rejects, defers, or expands deploy-layer corpus
     coverage.
   - Status: present in `standards/recognition-candidate-review.md`,
     `workflows/review-recognition-candidates.md`,
     `recognition-candidates/README.md`, and
     `scripts/02.rag-rulebook/validate-recognition-candidates/`.

7w. Add recognition-candidate review report helper.
   - Add a read-only helper that validates candidates, then summarizes pending
     candidates, coverage status, review needs, and allowed next actions.
   - Use the helper before changing candidate decisions or curated sources.
   - Keep the helper non-mutating so candidate promotion remains a governed
     review action.
   - Status: present in
     `scripts/02.rag-rulebook/report-recognition-candidates/`.

7x. Defer the MCP server recognition candidate.
   - Move the MCP server candidate to `deferred/` instead of accepting it into
     curated domain-noun vocabulary.
   - Preserve covered RAG/rulebook planning evidence while recording that
     deploy-layer corpus depth is still needed before curated deploy guidance.
   - Keep deferred candidates usable as review signals without making them
     active curated vocabulary.
   - Status: present in
     `recognition-candidates/deferred/2026-06-26-mcp-server.yml`.

7y. Add a local RAG/runtime build command.
   - Build a local deterministic runtime cache before any deployed RAG service
     is attempted.
   - Generate or check recognition sources, rulebook index, chunk set,
     runtime manifest, and validation report.
   - Write local runtime outputs to an ignored cache such as
     `.cache/02.rag-rulebook/`.
   - Fingerprint retrieval policy, recognition sources, recognition
     candidates, corpus gaps, generated index, and generated chunk set so
     query-time selector inputs cannot silently drift from build-time runtime
     state.
   - Keep the command deterministic and offline; do not add embeddings,
     network calls, or hosted service dependencies in this step.
   - Status: present in
     `scripts/02.rag-rulebook/build-local-runtime/`.

7z. Add a local context-query command.
   - Query the local runtime with request text, session metadata, focused
     paths, and token budget.
   - Return a validated `rag-rulebook/context-packet/v1` packet.
   - Reuse retrieval-selector fixture behavior until production retrieval
     runtime exists.
   - Refuse to query when live selector inputs or runtime outputs no longer
     match the local runtime manifest fingerprints.
   - Keep this as the local agent-facing interface while deploy corpus
     coverage matures.
   - Status: present in
     `scripts/02.rag-rulebook/query-local-context/`.

7aa. Govern local runtime freshness lifecycle.
   - Treat runtime fingerprints as a query-time safety fallback, not the
     default update mechanism.
   - Make the normal workflow detect changed RAG inputs before query,
     packaging, or deployment. Inputs include retrieval policy, policy
     dimensions, recognition sources, recognition candidates, corpus gaps,
     rulebook index inputs, and chunk-generation inputs.
   - When those inputs changed, rebuild the local runtime or require a rebuild
     before continuing.
   - Verify the rebuilt runtime manifest fingerprints before allowing
     `query-local-context`, corpus packaging, or deploy-readiness work to
     consume the runtime.
   - Fail closed if a stale runtime reaches query time anyway.
   - Fingerprint rulebook source roots, rule roots, migration maps,
     derivation reports, index/chunk generator scripts, and rulebook schemas
     as runtime inputs, not only selector-side inputs.
   - Add regression proof that changing a structured rule file makes an
     existing runtime report stale before source-material coverage work begins.
   - Fingerprint source projection manifests and source projection/coverage
     commands so projection governance cannot drift while runtime freshness
     still reports fresh.
   - Fingerprint validation machinery that changes the meaning of valid or
     fresh, including retrieval-policy, recognition-source, candidate,
     derivation-report, source-projection, source-material coverage,
     context-packet, selector fixture, evaluator, local query, runtime build,
     and runtime freshness scripts.
   - Status: strict freshness checking is present in
     `scripts/02.rag-rulebook/check-runtime-freshness/`,
     `scripts/02.rag-rulebook/build-local-runtime/`, and
     `scripts/02.rag-rulebook/query-local-context/`; the RAG/rulebook commit
     gate smoke-tests the freshness checker and deploy readiness requires
     freshness proof. Source projection and validation machinery fingerprint
     expansion is present. Automatic rebuild and later severity-aware drift
     tolerance remain planned.

7ab. Add versioned runtime drift severity policy.
   - Do not treat every runtime fingerprint deviation as the same class of
     failure forever.
   - Keep the first proactive freshness gate strict and fail-closed, but make
     its report shape ready for severity classification.
   - Define a versioned drift policy that can classify changes as fresh,
     minor drift, rebuild recommended, rebuild required, or blocked.
   - Let callers apply different tolerance levels by context: local planning
     may allow known minor drift with a warning, commit gates may allow only
     categorized non-blocking drift, and packaging or deployment must fail
     closed on uncategorized or high-risk drift.
   - Classify retrieval policy, chunk generation, deploy rules, MCP exposure,
     authentication, authorization, and runtime output changes as high-risk
     until a governed policy says otherwise.
   - Record drift decisions in reviewable policy files so constant business
     input can flow into the RAG system without making every source update a
     deploy blocker.
   - Status: planned after the first strict
     `scripts/02.rag-rulebook/check-runtime-freshness/` gate exists.

7ac. Govern source-material coverage and rule discovery drift.
   - Do not rely on runtime freshness alone to prove that source knowledge was
     actually promoted into retrievable rules.
   - Detect when source-material files are added, modified, moved, or removed
     under governed corpus roots such as `docs/02.rag-rulebook/source-material/`.
   - Require each source-material change to have one governed outcome:
     structured rulebook YAML, an explicit corpus gap, a derivation report
     explaining why no rule changed, or a retirement/removal record.
   - Detect when structured rule YAML files are added, modified, moved, or
     removed under indexed roots such as `docs/02.rag-rulebook/rules/` and
     `docs/04.deploy/rules/`.
   - Verify that indexed rule roots discover the changed YAML files and that
     generated chunk candidates/chunks include the expected derived rule
     material or intentionally exclude it with a recorded reason.
   - Treat new corpus roots as unindexed until they are explicitly registered
     in the index generator, corpus package policy, and commit gates.
   - Treat removed or moved rules as high-risk until references, rule packs,
     graph edges, chunks, evaluations, recognition sources, and derivation
     reports have been checked for orphaned references.
   - Add an executable coverage gate under
     `scripts/02.rag-rulebook/check-source-material-coverage/`, before relying
     on commit-time runtime freshness as proof that all relevant knowledge was
     captured.
   - Status: first executable gate present in
     `scripts/02.rag-rulebook/check-source-material-coverage/` and wired into
     `scripts/02.rag-rulebook/commit-gates/script.sh`. The gate proves
     current non-README source material has a structured rule, derivation
     report, or corpus gap outcome, and proves claimed structured rules reach
     the generated index and chunk set. `check-corpus-root-changes` now detects
     changed governed corpus-root paths and requires accepted retirement
     records for deleted or renamed old paths. Per-file source hashes and
     generated-YAML provenance continue under 7ad.

7ad. Treat source material as canonical and YAML rules as generated projections.
   - Make approved Markdown source material the canonical human-authored source
     for corpus knowledge.
   - Treat structured rulebook YAML as generated or workflow-produced
     intermediate artifacts, not independent editorial source of truth.
   - Require generated YAML rules to carry provenance back to the source
     material path, source content hash, derivation workflow or policy version,
     generated timestamp, and generator identity.
   - Carry that provenance forward into the rulebook index, generated chunks,
     runtime manifest, deploy-readiness proof, and future corpus packages.
   - Detect source-material changes by comparing folder-level fingerprints and
     per-file hashes, then require regenerated YAML, updated derivation reports,
     updated corpus gaps, or explicit retirement records before commit or
     packaging can proceed.
   - Detect manual YAML edits that do not match source-material provenance as
     generated-artifact drift unless a governed emergency/manual override is
     recorded.
   - Keep source hashes and derivation provenance generated by tooling rather
     than asking humans to hand-maintain hash values in YAML files.
   - Status: first provenance enforcement present. Current source-derived YAML
     rules carry `source_derivation` with derivation workflow, derivation
     report, source paths, and source SHA-256 hashes.
     `scripts/02.rag-rulebook/check-source-material-coverage/` recomputes
     source hashes and fails stale projections. The rulebook index and chunk
     generators carry `source_derivation` into generated artifacts and chunks.
     Source-to-rule relationships are now registered in
     `.agentic/02.rag-rulebook/source-projections/v1.yml` and checked by
     `scripts/02.rag-rulebook/check-source-projections/`. A fully automated
     source-to-YAML generator and emergency/manual override workflow remain
     planned.

7ae. Add retirement records for removed or superseded RAG artifacts.
   - Govern source material, rules, rule packs, derivation reports, corpus
     gaps, recognition sources, evaluations, generated indexes, chunks,
     runtime caches, workflows, and scripts that stop being active.
   - Require prior artifact hashes, replacement paths when knowledge moved,
     active-reference checks, validation evidence, and review decisions.
   - Run retirement validation at the RAG/rulebook commit boundary so deleted
     source or rule material cannot become an unexplained retrieval gap.
   - Status: present in `schemas/retirement-record.schema.yml`,
     `retirements/`, and
     `scripts/02.rag-rulebook/validate-retirement-records/`. Source
     projection checks now require retired projection-set paths to have
     accepted retirement records and reject active projection sets that still
     name retired artifacts.

7ae. Add source projection manifest checking.
   - Register every active governed source-material file in an explicit
     source projection manifest.
   - For each projection, name the owning corpus, expected YAML rule outputs,
     derivation reports, corpus gaps, selector evaluations, and required proof
     commands.
   - Fail the commit gate when a source file is not registered, a
     source-derived YAML file is not registered, a declared output is missing,
     a YAML projection has stale source hashes, or a derivation report does
     not mention the projection source and target rules.
   - Keep this as a read-only check first; write-mode regeneration remains a
     later governed step.
   - Status: present in
     `.agentic/02.rag-rulebook/source-projections/v1.yml`,
     `schemas/source-projection-manifest.schema.yml`,
     `guides/source-projection-manifest.md`, and
     `scripts/02.rag-rulebook/check-source-projections/`.

7af. Add derived rule projection planning.
   - Add a read-only command that consumes the active source projection
     manifest and emits a deterministic projection plan.
   - The plan should include source paths, current source hashes, expected
     derived YAML paths, derivation report status, current YAML provenance
     state, provenance templates, and required actions.
   - Start with check-only behavior that fails when any active projection is
     mechanically stale or incomplete.
   - Do not let this first command semantically rewrite rules; semantic
     source-to-rule changes still require derivation reports and review.
   - Status: present in
     `scripts/02.rag-rulebook/generate-derived-rules/` and wired into
     `scripts/02.rag-rulebook/commit-gates/script.sh`.

7ag. Add provenance-only apply mode for derived rules.
   - Add an explicit write mode that updates only existing top-level
     `source_derivation` blocks for declared rule paths.
   - Do not create derived rule files, rewrite semantic rule content, or accept
     source-to-rule meaning changes without derivation reports.
   - Re-run source projection checks after applying provenance so a stale hash
     can be repaired but missing or orphaned outputs still fail closed.
   - Keep `--check` as the default commit-gate behavior; apply mode is an
     explicit maintenance action.
   - Status: present in
     `scripts/02.rag-rulebook/generate-derived-rules/script.sh` and covered by
     `scripts/02.rag-rulebook/generate-derived-rules/smoke-test.sh`.

7ah. Add source-to-rule work-order generation.
   - Add a read-only command that turns the active source projection manifest
     into a semantic derivation work order.
   - Include source material paths, SHA-256 hashes, source outlines, expected
     derived YAML paths, derivation report state, corpus gaps, selector proof
     paths, required checks, and ordered next actions.
   - Keep this command as the handoff between deterministic scripts and
     agent/human semantic derivation. It must not write YAML rules, derivation
     reports, chunks, evaluations, or provenance.
   - Run the work-order command and smoke test from the RAG/rulebook commit
     gate so the source-to-rule update path stays executable.
   - Status: present in
     `scripts/02.rag-rulebook/generate-source-to-rule-work-order/`.

7ai. Add source-to-rule draft packet generation.
   - Add a read-only command that consumes the source-to-rule work order and
     packages the bounded source material, current YAML projections,
     derivation reports, corpus gaps, selector evaluations, draft objectives,
     banned actions, work actions, and required checks needed for semantic
     proposal work.
   - Keep this command as an agent/sub-agent input packet, not an automatic
     YAML writer. It must not write source material, rules, reports, chunks,
     evaluations, provenance, packages, runtime outputs, or deploy artifacts.
   - Run the draft-packet command and smoke test from the RAG/rulebook commit
     gate so the proposal path remains executable.
   - Treat this as the last corpus update-machine slice before returning to
     MSP shipping work unless a blocker appears.
   - Status: present in
     `scripts/02.rag-rulebook/generate-source-to-rule-draft-packet/`.

7aj. Add RAG-versus-source A/B context evaluation.
   - Add a reusable RAG/rulebook skill for planning, discovery, and
     investigation prompts.
   - Require two evidence paths before answering: a local RAG context packet
     from `query-local-context` and targeted direct source verification.
   - Compare where the paths agree, where they disagree, what each path
     missed, how the RAG path should improve, and an approximate token-saving
     estimate for using RAG instead of broad source reading.
   - Keep source files authoritative while the RAG runtime matures, and turn
     repeated RAG misses into corpus gaps, recognition candidates, chunking
     improvements, or evaluation fixtures.
   - Status: present in `.agentic/02.rag-rulebook/skills/ab-context-evaluation.md`
     and wired into `.agentic/02.rag-rulebook/workflows/default.md`.

7ak. Demote session metadata behind request context for retrieval.
   - Keep session metadata for chat/worktree provenance, fallback routing, and
     execution safety.
   - Build a fresh request context for each retrieval attempt from prompt
     intent, focused paths, exact corpus/artifact/path terms, and side-effect
     classification.
   - Let explicit request context beat session defaults for retrieval target
     selection while preserving session workflow gates for edits, commits,
     deploys, destructive actions, and infrastructure mutation.
   - Prove exact cross-session corpus retrieval with an evaluation fixture and
     keep broad nouns from crossing corpus boundaries without supporting
     evidence.
   - Status: present in
     `policies/retrieval-selector/v1/dimensions/request-context.yml`,
     `policies/retrieval-selector/v1.yml`, and
     `evaluations/retrieval-selector/v1/fixtures/request-context-exact-corpus-cross-session.yml`.

7al. Add question-category evidence bundles.
   - Add a reusable question-category recognition path so recurring question
     shapes can require canonical evidence families without one-off prompt
     patches.
   - Use curated question-category and evidence-family terms to map questions
     such as architecture-boundary placement into required source paths before
     final ranking.
   - Emit missing-evidence gaps and lower retrieval confidence when an expected
     evidence family is absent, filtered, or trimmed.
   - Prove the mechanism with a fixture where a RAG Query apps/platform question
     retrieves apps, platform, and dependency-direction evidence even though the
     session remains `02.rag-rulebook`.
   - Status: present in
     `recognition-sources/curated/question-categories.yml`,
     `policies/retrieval-selector/v1/dimensions/evidence-bundles.yml`,
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh`,
     and
     `evaluations/retrieval-selector/v1/fixtures/question-category-architecture-boundary.yml`.

7am. Require compiled selector policy before production runtime use.
   - Make governed YAML the source of selector behavior, with runtime code
     executing compiled policy instead of duplicating precedence, intent
     resolution, evidence bundle, corpus-routing, or confidence behavior in
     hidden constants.
   - Treat hard-coded selector behavior as allowed only when it is local
     runtime glue that consumes compiled policy, not as independent selector
     doctrine.
   - Compile validated policy packs, imported dimensions, generated and
     curated recognition sources, corpus ownership, rule graph metadata, and
     selector feature flags before local runtime or hosted runtime query use.
   - Require compiled policy provenance so packets and A/B evaluations can
     explain which policy inputs shaped retrieval.
   - Status: present in
     `schemas/compiled-retrieval-policy.schema.yml`,
     `scripts/02.rag-rulebook/compile-retrieval-policy/`,
     `scripts/02.rag-rulebook/build-local-runtime/`, and
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/`.

7an. Add retrieval strategy policy and selector trace.
   - Define a reusable staged retrieval strategy in governed policy so the
     selector can move through exact identifiers, generated concepts, curated
     concepts, bounded graph expansion, evidence bundles, and final ranking.
   - Compile the retrieval strategy into the local runtime policy artifact.
   - Emit a compact selector trace in context packets with stage IDs, stage
     statuses, recognition counts, candidate counts, required evidence, and
     selected chunk IDs.
   - Extend retrieval selector evaluations so fixtures can assert required
     stage IDs and applied stages.
   - Add cross-session architecture-boundary fixture coverage so this is a
     reusable retrieval-shape improvement, not a one-off platform question
     patch.
   - Status: present in
     `policies/retrieval-selector/v1/dimensions/retrieval-strategy.yml`,
     `scripts/02.rag-rulebook/compile-retrieval-policy/`,
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/`,
     `scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/`, and
     `evaluations/retrieval-selector/v1/fixtures/question-category-capability-placement-cross-session.yml`.

7ao. Add compact context packet output for agent use.
   - Keep full JSON packets available for debugging, provenance, selector
     trace review, and evaluation failure analysis.
   - Add a compact output mode that returns selected chunk content, concise
     citations, confidence, gaps, required checks, and stop conditions without
     the full debug/provenance payload.
   - Use A/B context evaluation to compare full debug packet tokens,
     selected-content tokens, and source-verification tokens so compact packet
     savings are visible.
   - Preserve selector trace access on demand so retrieval misses can still be
     diagnosed without making every ordinary agent query consume the full
     debug packet.
   - Status: planned.

7ap. Add policy-plus-implementation evidence bundles.
   - Recognize questions that ask how a policy works, how it is implemented,
     or how a governed concern should be explained.
   - Require source verification and retrieval to cover concept definition,
     layer ownership, implementation mechanics, verification expectations, and
     forbidden actions before answering.
   - Add evidence-family coverage for every runtime module listed in
     `docs/harness/architecture/rules/layers/platform.yml`: contracts, config,
     runtime, server, security, observability, health, workers, and testing.
   - Prove the miss class with a logging-policy fixture that requires
     reporting/analytics/audit concern evidence and platform implementation
     evidence, while keeping packages/core logger-contract evidence available
     only when the prompt names logger contracts or redaction contracts.
   - Prove platform module coverage with a matrix fixture that requires every
     runtime module family from `platform.yml` to be recognized and bundled:
     contracts, config, runtime, server, security, observability, health,
     workers, and testing.
   - Status: present in
     `skills/ab-context-evaluation.md`,
     `recognition-sources/curated/question-categories.yml`,
     `policies/retrieval-selector/v1/dimensions/evidence-bundles.yml`, and
     `evaluations/retrieval-selector/v1/fixtures/question-category-logging-policy-implementation.yml`
     plus
     `evaluations/retrieval-selector/v1/fixtures/question-category-platform-runtime-modules-policy-implementation.yml`.

7aq. Add generic intra-source rule reranking.
   - Improve accuracy after evidence bundles select the right source file by
     re-ranking rule chunks inside required sources.
   - Use generated rule metadata rather than prompt-specific hard-coded rule
     mappings: rule IDs, titles, summaries, `must`, `must_not`, and
     `agent_guidance` fields.
   - Add an `intra-source-reranking` strategy stage between
     `evidence-bundles` and `final-ranking` so A/B diagnosis can distinguish
     right-file/wrong-section misses from recognition or bundle misses.
   - Extend retrieval fixtures so they can require selected rule IDs, proving
     that the exact section survives selection.
   - Prove the behavior with logging, platform server, and platform workers
     fixtures so the improvement is not specific to a single logging prompt.
   - Status: present in
     `scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh`,
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh`,
     `scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh`,
     `policies/retrieval-selector/v1/dimensions/retrieval-strategy.yml`,
     `evaluations/retrieval-selector/v1/fixtures/question-category-logging-policy-implementation.yml`,
     `evaluations/retrieval-selector/v1/fixtures/question-category-platform-server-policy-implementation.yml`,
     and
     `evaluations/retrieval-selector/v1/fixtures/question-category-platform-workers-policy-implementation.yml`.

7ar. Add generated projection-set suggestions for new source material.
   - Detect new or changed governed source material and generate suggested
     source projection manifest entries before semantic derivation begins.
   - Keep suggestions review-only: do not auto-accept owning corpus, expected
     rule paths, derivation reports, selector fixtures, or corpus gaps without
     agent/human review.
   - Use source path, heading outline, artifact metadata, corpus root, and
     existing projection patterns to propose bounded projection sets.
   - Add commit-gate guidance that distinguishes orphan-source blockers from
     suggested projection candidates, so new source material can move through a
     governed queue instead of becoming manual bookkeeping.
   - Status: planned after the first MSP shipping path is established.

7as. Add OKF source-material quality review loop.
   - Treat source material as the canonical human-authored input to the OKF,
     not as retrieval-ready coverage by itself.
   - Require iterative review by architect, agentic engineer,
     SecOps engineer, and senior SRE roles before production source material
     can proceed to source-to-rule derivation.
   - Assess coverage, necessity, production-grade gaps, execution variables,
     human readability, machine readability, cost optimization, security,
     performance, and token optimization.
   - Require every reviewer to score above 9.5/10 and record no blocking gaps.
   - Store review records under
     `.agentic/02.rag-rulebook/source-material-reviews/`.
   - Apply recommendations and rerun all reviewers until the threshold is met.
   - Status: present in `standards/okf-source-material-quality.md`,
     `workflows/review-okf-source-material.md`,
     `schemas/okf-source-material-review.schema.yml`,
     `source-material-reviews/README.md`, and
     `scripts/02.rag-rulebook/validate-okf-source-material-reviews/`.

8. Add deploy-layer corpus gap tracking.
   - Track the deferred MCP server candidate's missing deploy-layer depth as a
     governed `corpus.04.deploy` gap.
   - Define the required source material, structured rules, chunks,
     evaluation fixtures, GitHub deployment checks, AWS environment boundaries,
     rollback expectations, and stop conditions needed before curated deploy
     guidance is safe.
   - Use the local RAG runtime and local context-query command while building
     this deploy corpus.
   - Status: present in
     `corpus-gaps/04.deploy/mcp-server-deployment.yml`,
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh`,
     and `retrieval-selector.v1.intent-form-planning-mcp-server`.

8a. Add first deploy corpus source material.
   - Start `corpus.04.deploy` with production-grade source material for MCP
     server deployment through GitHub and AWS.
   - Organize deploy source material by deploy track, not separate owning
     layers: shared, `00.chat`, `02.rag-rulebook`, and `03.product`.
   - Keep the source material non-executable: no AWS mutation, no GitHub
     workflow implementation, and no production MCP endpoint.
   - Define scope, non-goals, deployment phases, GitHub and AWS boundaries,
     security expectations, observability, rollback, stop conditions, and
     known gaps before structured rule conversion.
   - Status: present in
     `docs/04.deploy/source-material/02.rag-rulebook/mcp-server-deployment.md`
     and
     `corpus-gaps/04.deploy/mcp-server-deployment.yml`.
   - Note: existing source material predates the OKF quality review loop. New
     production-grade vertical source material, including GitHub Actions to ECS
     Fargate deployment guidance, must pass the OKF review loop before YAML
     derivation.

8b. Add first deploy corpus structured rulebook coverage.
   - Convert the `02.rag-rulebook` deploy source material into structured
     `corpus.04.deploy` YAML rules.
   - Keep deploy governance owned by `04.deploy` while naming
     `02.rag-rulebook` as the deployment track.
   - Capture local-first RAG, published corpus packages, remote context
     packets, read-only MCP-first exposure, governed MCP tools, GitHub release
     control, AWS runtime boundaries, observability, rollback, and readiness
     gaps.
   - Status: present in
     `docs/04.deploy/rules/02.rag-rulebook/mcp-server-deployment.yml` and
     `corpus-gaps/04.deploy/mcp-server-deployment.yml`.

8c. Add source-to-rule derivation and drift review governance.
   - Define the required report shape for turning approved source material
     into structured rules.
   - Require semantic drift and conflict review before downstream rules,
     rulesets, generated indexes, chunks, selector evaluations, or published
     corpus packages are treated as current.
   - Add a first pending derivation report for the MCP server deployment source
     conversion.
   - Status: present in
     `standards/source-to-rule-derivation.md`,
     `workflows/derive-rules-from-source.md`,
     `schemas/source-to-rule-derivation-report.schema.yml`, and
     `derivation-reports/04.deploy/2026-06-26-mcp-server-deployment.yml`.

8d. Add source-to-rule derivation report validation.
   - Add a read-only validator for
     `rag-rulebook/source-to-rule-derivation-report/v1` records.
   - Wire derivation-report validation into the RAG/rulebook commit gate when
     `.agentic/02.rag-rulebook/derivation-reports` exists.
   - Add smoke coverage for valid reports and broken report cases.
   - Status: present in
     `scripts/02.rag-rulebook/validate-derivation-reports/` and
     `scripts/02.rag-rulebook/commit-gates/script.sh`.

8e. Add deploy corpus index and chunk coverage.
   - Teach the rulebook index generator to scan numbered corpus rule roots,
     including `docs/04.deploy/rules/` as `corpus.04.deploy`.
   - Keep `docs/02.rag-rulebook/rules/` mapped to `corpus.02.rag-rulebook`
     so deploy chunks do not get mixed into the RAG/rulebook service corpus.
   - Add smoke assertions that prove deploy MCP rules are indexed and chunked
     with `corpus_id: corpus.04.deploy`.
   - Status: present in
     `scripts/02.rag-rulebook/generate-rulebook-index/script.sh`,
     `scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh`, and
     `scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`.

8f. Add deploy MCP selector evaluation proof.
   - Let matching governed corpus-gap records admit their target corpus into
     selector candidate filtering without letting broad layer words admit
     unrelated corpora.
   - Update the MCP planning fixture so it requires both RAG/rulebook MCP
     architecture chunks and the first deploy MCP chunk.
   - Keep the deploy corpus gap open until deeper GitHub-to-AWS deployment
     rules, AWS runtime boundaries, and deploy-execution evaluations exist.
   - Status: present in
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh`,
     `evaluations/retrieval-selector/v1/fixtures/intent-form-planning-mcp-server.yml`,
     and `corpus-gaps/04.deploy/mcp-server-deployment.yml`.

8g. Split deploy corpus depth into GitHub and AWS concerns.
   - Add a GitHub-to-AWS release-control ruleset for protected environments,
     OIDC preference, staged workflow boundaries, artifact provenance, and
     readiness blocking.
   - Add an AWS runtime boundary ruleset for target identity, network exposure,
     secrets, observability, health checks, and rollback proof.
   - Keep these rules non-executable until deploy-execution selector fixtures,
     deployment-readiness checks, and AWS workflow coverage exist.
   - Status: present in
     `docs/04.deploy/rules/02.rag-rulebook/github-to-aws-deployment.yml`,
     `docs/04.deploy/rules/02.rag-rulebook/aws-runtime-boundaries.yml`,
     `corpus-gaps/04.deploy/mcp-server-deployment.yml`, and
     `derivation-reports/04.deploy/2026-06-26-mcp-server-deployment.yml`.

8h. Add remote-main-to-AWS deployment readiness checks.
   - Add a deploy readiness ruleset for exact remote main SHA, branch and
     status-check proof, runtime-family selection, IaC ownership, immutable
     artifact promotion, supply-chain evidence, governed secrets, MCP
     threat-model and access-control proof, cost, capacity, quota controls,
     operational runbooks, and prose-to-command-surface maturity.
   - Keep readiness checks owned by `corpus.04.deploy` while preserving the
     `02.rag-rulebook` deploy track.
   - At this step, keep deploy execution blocked until deploy-execution
     selector fixtures and AWS workflow coverage exist.
   - Status: present in
     `docs/04.deploy/rules/02.rag-rulebook/deployment-readiness-checks.yml`,
     `corpus-gaps/04.deploy/mcp-server-deployment.yml`, and
     `derivation-reports/04.deploy/2026-06-26-mcp-server-deployment.yml`.

8i. Add deploy-execution selector blocking proof.
   - Recognize prompts shaped as `Deploy the ...` as deploy execution.
   - Resolve conflicting intent forms by governed precedence so explicit
     no-action, explanation, and planning prompts beat broad deploy wording.
   - Emit `action_authorization` so side-effect permission is explicit and
     downstream workflows do not infer execution permission from routing alone.
   - Let blocking corpus gaps name exact evidence chunks that must survive
     ranking and token trimming.
   - Attach selected evidence chunks and citations directly to blocking gaps.
   - Prove `Deploy the RAG rulebook MCP server to AWS from main.` routes to
     `04.deploy`, selects deploy and MCP architecture evidence, and blocks on
     missing AWS runtime target, GitHub workflow, executable deploy checks,
     transport/auth proof, and cost/capacity/quota boundary.
   - Prove `How do I deploy ...`, `Can you explain how to deploy ...`,
     `Prepare a deployment plan ...`, and `Do not deploy ...` retrieve deploy
     context without becoming deploy execution.
   - Keep deploy execution blocked until an actual GitHub Actions workflow,
     protected target environment, selected AWS runtime, and target-specific
     deploy-readiness manifest pass executable checks.
   - Status: present in
     `schemas/context-packet.schema.yml`,
     `recognition-sources/curated/intent-forms.yml`,
     `scripts/02.rag-rulebook/generate-retrieval-selector-fixture/script.sh`,
     `scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh`,
     `evaluations/retrieval-selector/v1/fixtures/deploy-execution-mcp-server-blocked.yml`,
     `evaluations/retrieval-selector/v1/fixtures/intent-form-deploy-planning-question.yml`,
     `evaluations/retrieval-selector/v1/fixtures/intent-form-deploy-explanation-question.yml`,
     `evaluations/retrieval-selector/v1/fixtures/intent-form-deploy-plan-request.yml`,
     `evaluations/retrieval-selector/v1/fixtures/intent-form-deploy-negation.yml`,
     and `corpus-gaps/04.deploy/mcp-server-deployment.yml`.

8j. Add concrete GitHub-to-AWS workflow coverage and executable deploy checks.
   - Add a deploy-owned AWS workflow for RAG/rulebook service deployment that
     names required inputs, GitHub release control, OIDC preference, immutable
     artifacts, AWS target boundaries, MCP exposure, rollback, disablement, and
     stop conditions.
   - Add a read-only deploy-readiness verifier that accepts a target manifest,
     validates GitHub, artifact, AWS, MCP, operations, and local-check proof,
     and fails closed unless the report status is ready.
   - Verify GitHub source policy/ref consistency, named OIDC audience and trust
     conditions, governed MCP transport values, and runtime-specific AWS target
     proof.
   - Enforce the governed MCP specification version value in the readiness
     verifier.
   - Keep `--allow-blocked` limited to callers that explicitly declare
     planning or explanation intent, and emit `exit_overridden_for_planning`
     so deploy jobs can reject non-ready reports.
   - Run local runtime build, local runtime freshness, and local context query
     smoke tests from the RAG/rulebook commit gate so the local bridge to
     hosted RAG cannot drift while selector-only tests still pass.
   - Keep deploy execution blocked until the actual GitHub Actions workflow,
     protected environment configuration, selected AWS runtime target, and
     passing target manifest exist.
   - Status: present in
     `.github/workflows/rag-rulebook-msp-checks.yml`,
     `.agentic/aws/workflows/deploy-rag-rulebook-service.md`,
     `scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh`,
     `scripts/04.deploy/verify-rag-rulebook-deploy-readiness/smoke-test.sh`,
     `docs/04.deploy/rules/02.rag-rulebook/github-to-aws-deployment.yml`,
     `docs/04.deploy/rules/02.rag-rulebook/deployment-readiness-checks.yml`,
     and `corpus-gaps/04.deploy/mcp-server-deployment.yml`.

9. Plan the prototype corpus migration.
   - Separate harness-owned rules from `corpus.03.product`,
     `corpus.03.product.design-system`, `corpus.04.deploy`, and
     `corpus.05.education`.
   - Include `corpus.02.rag-rulebook` as a self-corpus for service governance.
   - Use artifact path migration before moving committed files.

10. Only after the above, design a standalone service or repo extraction.
   - The service should consume corpus packages, generated indexes, chunks,
     retrieval policies, recognition sources, and evaluation results.
   - The workbench should call the service; it should not own the service.
   - The first hosted shape should expose a provider-agnostic HTTP API for
     context packets before exposing MCP tools.
   - A future MCP surface should wrap the same internal API capabilities rather
     than duplicating retrieval logic.
   - Local repos should use a tiny bootstrap and safe fallback rules rather
     than carrying the full harness forever.
   - Credentials must live outside `AGENTS.md`, `CLAUDE.md`, source material,
     chunks, logs, and fixtures. Use environment variables, local config,
     keychain/SSO, GitHub environment secrets, or short-lived cloud identity.
   - Deployment to GitHub/AWS should wait until local runtime behavior,
     deploy-corpus checks, API contract, authentication model, and runtime
     target are proven.

11. Shape the first MVP service.
   - Target: provider-agnostic governed context for coding agents.
   - First hosted AWS runtime target: ECS Fargate. App Runner remains a
     legacy/existing-service verifier value, but it is not the preferred target
     for this new MSP because AWS is no longer accepting new App Runner
     customers after April 30, 2026.
   - User flow: engineer creates an account, installs a small local client,
     adds bootstrap instructions to `AGENTS.md` or `CLAUDE.md`, points local
     config at the hosted service, authenticates, and retrieves validated
     context packets.
   - Local client responsibilities: identify repo, commit, branch, task,
     session layer/mode/workflow, focused paths, token budget, and fallback
     policy; call the service; validate the returned packet; fail safely.
   - Hosted service responsibilities: own corpora, rulebooks, chunks,
     retrieval policy, evaluations, freshness, account/repo/project settings,
     and versioned best-practice packs.
   - First API surface: `/health`, `/version`, and `/context/query`.
   - Later API surface: corpus inspection, gap inspection, package inspection,
     rule/chunk search, context validation, evaluation reports, and deploy
     readiness.
   - MCP should be a later access surface over the same service capabilities,
     starting read-only before any write-capable or deploy-capable tools.
   - Status: ECS Fargate selected as the first hosted target after local
     runtime test and GitHub Actions skeleton. Thin local-only service API
     skeleton is present in `.agentic/02.rag-rulebook/service/` and
     `scripts/02.rag-rulebook/run-local-service/`. It is loopback-first,
     validates request shape, fails closed on stale runtime, and requires an
     explicit token for non-loopback development binds. Hosted auth, account
     management, AWS deployment, and MCP exposure remain pending.
   - Structure rule: keep RAG/rulebook service machinery inside the
     `02.rag-rulebook` layer until a governed extraction creates a standalone
     service repo. Do not create root `apps/` or `platform/` runtime folders in
     this harness repo for the RAG/rulebook MSP.
   - Infra rule: actual deployment implementation belongs under `infra/`, not
     under `.agentic/`, `docs/`, `apps/`, or `platform/`. Use
     `infra/04.deploy/02.rag-rulebook/` for the first ECS Fargate deployment
     target, container packaging boundary, environment manifests, IaC, and
     GitHub Actions deploy templates. Keep `.github/workflows/` as the live
     GitHub workflow surface, but keep the reviewed deployment definition and
     templates under `infra/**`.

12. Introduce the first infra implementation boundary.
   - Create `infra/` as the implementation home for infrastructure-as-code,
     deployment definitions, container packaging boundaries, environment
     manifests, and deploy workflow templates.
   - Keep deploy knowledge in `docs/04.deploy/`, deploy process in
     `.agentic/aws/`, deploy checks in `scripts/04.deploy/`, and service
     runtime machinery in `.agentic/02.rag-rulebook/service/`.
   - Keep this slice non-mutating: no AWS calls, no GitHub deployment, no
     Terraform/CDK/Pulumi apply, no secrets, and no live production target.
   - Status: scaffold present in `infra/04.deploy/02.rag-rulebook/`.

13. Add the first deployable-service image boundary.
   - Package the existing local RAG/rulebook HTTP service without moving source
     code out of `.agentic/02.rag-rulebook/service/`.
   - Keep the container implementation under
     `infra/04.deploy/02.rag-rulebook/image/` and keep executable build/smoke
     commands under `scripts/02.rag-rulebook/`.
   - Support Git-less container runtime by allowing service and query scripts
     to resolve the repo root from `RAG_REPO_ROOT`.
   - Validate the container build context denylist before building.
   - Smoke-test the image by mounting a freshly built runtime cache read-only,
     then verifying health, version, token enforcement, and compact
     context-query behavior.
   - Keep this slice local-only: no registry push, no AWS call, no GitHub
     deployment, no secrets, and no live production target.
   - Status: present in `infra/04.deploy/02.rag-rulebook/image/`,
     `scripts/02.rag-rulebook/build-service-image/`, and
     `scripts/02.rag-rulebook/smoke-test-service-image/`.

14. Add the staging ECS Fargate deploy package.
   - Add a non-secret staging deploy-readiness manifest under
     `infra/04.deploy/02.rag-rulebook/environments/staging/`.
   - Reuse the existing `kanbien-staging-alb` and wildcard `*.kanbien.com`
     certificate for `rag.kanbien.com` instead of creating a second ALB.
   - Add CloudFormation templates for one-time GitHub OIDC bootstrap, reusable
     staging foundation resources, and the ECS service/task definition.
   - Add a manual GitHub Actions deployment workflow that assumes AWS through
     OIDC, applies the foundation stack, builds and pushes the service image,
     resolves the immutable ECR digest, deploys ECS, waits for stability, and
     checks `https://rag.kanbien.com/health`.
   - Keep the readiness manifest blocked until remote-main commit evidence,
     protected GitHub environment evidence, OIDC trust, generated runtime
     hashes, immutable image digest, ECS service evidence, rollback evidence,
     and health proof exist.
   - Status: present in
     `infra/04.deploy/02.rag-rulebook/environments/staging/deploy-readiness.yml`,
     `infra/04.deploy/02.rag-rulebook/ecs-fargate/cloudformation/`, and
     `.github/workflows/deploy-rag-rulebook-staging.yml`.

15. Make the service image self-contained for ECS.
   - Build the deterministic RAG/rulebook runtime cache inside the image so ECS
     does not depend on a local bind mount.
   - Keep the mounted-runtime image smoke test as a fallback development check,
     but treat image-embedded runtime as the hosted MSP path.
   - Status: present in
     `infra/04.deploy/02.rag-rulebook/image/Dockerfile`.

## Non-Goals For The Current Stage

- Do not execute AWS or GitHub mutations without the approved AWS execution
  workflow and explicit current-chat approval for the exact commands.
- Do not build an MCP server.
- Do not move `docs/harness/architecture/` files.
- Do not introduce embeddings before deterministic indexes and chunks exist.
- Do not merge domain corpora into one instruction set.
- Do not deploy RAG to AWS before local runtime behavior, deploy-corpus checks,
  GitHub environment protection, OIDC trust, immutable image digest, rollback
  evidence, and health checks are proven.
- Do not derive production-grade deploy YAML from source material that has not
  passed the OKF source-material review loop.

## Next Small Slice

Validate and review the staging deploy package, then run the approved AWS
bootstrap only after the exact commands and rollback path are accepted.

That slice should:

- validate the CloudFormation templates without mutating AWS
- validate the staging deploy-readiness manifest in planning mode
- configure the GitHub `staging` environment and
  `RAG_RULEBOOK_AWS_DEPLOY_ROLE_ARN` repository variable
- apply `github-oidc-bootstrap.yml` with `gordon-kanbien` only after explicit
  AWS execution approval
- merge/push the workflow to remote `main`
- run the manual deploy workflow
- update the readiness manifest with the real commit, image digest, runtime
  hashes, ECS task/service evidence, rollback target, and health result
