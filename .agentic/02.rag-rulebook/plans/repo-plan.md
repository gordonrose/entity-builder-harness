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

The deterministic foundation is now strong enough to bootstrap local RAG before
deployment. Local RAG should come before deploy-corpus expansion so agents can
use validated local context packets while the deploy corpus is being built.

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
   - Keep this as the local agent-facing interface while deploy corpus
     coverage matures.
   - Status: present in
     `scripts/02.rag-rulebook/query-local-context/`.

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

9. Plan the prototype corpus migration.
   - Separate harness-owned rules from `corpus.03.product`,
     `corpus.03.product.design-system`, `corpus.04.deploy`, and
     `corpus.05.education`.
   - Include `corpus.02.rag-rulebook` as a self-corpus for service governance.
   - Use artifact path migration before moving committed files.

10. Only after the above, design a standalone service or repo extraction.
   - The service should consume corpus packages and generated indexes.
   - The workbench should call the service; it should not own the service.
   - Deployment to GitHub/AWS should wait until local runtime behavior and
     deploy-corpus checks are proven.

## Non-Goals For The Current Stage

- Do not build the deployed RAG server.
- Do not build an MCP server.
- Do not move `docs/harness/architecture/` files.
- Do not introduce embeddings before deterministic indexes and chunks exist.
- Do not merge domain corpora into one instruction set.
- Do not deploy RAG to AWS before local runtime behavior and deploy-corpus
  checks are proven.

## Next Small Slice

Add deploy-execution selector proof and deployment-readiness checks so prompts
that ask to deploy the MCP/RAG service block with specific missing GitHub/AWS
readiness items instead of relying on planning-only guidance.
