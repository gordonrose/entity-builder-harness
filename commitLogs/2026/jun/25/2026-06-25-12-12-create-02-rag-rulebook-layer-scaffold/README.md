# Chat Session: 2026-06-25-12-12 create-02-rag-rulebook-layer-scaffold

<!-- agentic-session
id: 2026-06-25-12-12-create-02-rag-rulebook-layer-scaffold
task: create 02 rag rulebook layer scaffold
branch: chat/2026-06-25-12-12-create-02-rag-rulebook-layer-scaffold
worktree: /tmp/agentic-chat-worktrees/entity-builder-harness-001-1672151846/chat_2026-06-25-12-12-create-02-rag-rulebook-layer-scaffold-52906228
layer: harness
mode: implementation
workflow: .agentic/01.harness/workflows/change-harness.md
status: ready
raised_at_utc: 2026-06-25T11:12:51Z
codex_session_log_path: /home/owner/.codex/sessions/2026/06/25/rollout-2026-06-25T02-03-04-019efc4d-4c05-7003-b932-f9db433f587e.jsonl
latest_commit_at_utc: 2026-06-25T23:15:34Z
latest_commit_sha: f84184a
chat_duration: 43363s (00:12:02:43)
estimated_chat_tokens: 3295858 estimated from chat transcript bytes (13183431 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/25/rollout-2026-06-25T02-03-04-019efc4d-4c05-7003-b932-f9db433f587e.jsonl)
estimated_chat_cost: USD 98.88 estimated from estimated_chat_tokens
estimated_chat_cost_basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing
-->

## Initial Intent

create 02 rag rulebook layer scaffold

## Session Log

- Session started.
- Branch created.
- Chat-owned worktree created.
- Commit log initialized.

## Questions Asked

- None recorded yet.

## Issues Raised

- None recorded yet.

## Decisions Made

- Add RAG/Rulebook as first-class layer `02.rag-rulebook`.
- Renumber existing product, deploy, education, and shared metadata layers to
  `03.product`, `04.deploy`, `05.education`, and `06.shared`.
- Keep existing prototype rulebook artifacts in place until a separate governed
  corpus migration assigns final domain corpus homes.
- Add design-only RAG/Rulebook standards for the portable service contract and
  modular domain corpus package shape before building runtime code.
- Record the ordered repo plan for context-packet schema, rulebook index schema,
  read-only index generation, chunk generation, validation, and later corpus
  migration.
- Align domain corpus IDs with numbered layers, using names such as
  `corpus.01.harness`, `corpus.02.rag-rulebook`, and `corpus.03.product`.
- Include `corpus.02.rag-rulebook` as the self-corpus for the RAG/rulebook
  service's own governance, indexing, chunking, retrieval, validation, and
  packaging rules.
- Treat portable RAG/rulebook service and corpus package standards as reusable
  patterns for seed consumers, not required runtime artifacts for every target.
- Defer the final standalone RAG/rulebook service target name until the repo or
  service extraction boundary is explicit.
- Add a reusable `rag-rulebook/context-packet/v1` schema as the retrieval
  handoff contract. Context packets carry selected evidence, checks,
  forbidden actions, stop conditions, citations, confidence, gaps, budgets, and
  provenance; they do not perform the consuming workflow's final action.
- Teach context packets in two layers: structured `field_guide` entries inside
  the schema for machine-readable field explanations, plus a companion guide
  for human mental models, good and bad packet shapes, and LLM usage rules.
- Promote the schema teachability pattern into the harness artifact standard:
  new or materially changed schemas should include structured field
  explanations, validation rules where deterministic, a companion guide unless
  explicitly unnecessary, and metadata/index links between schema and guide.
- Add a read-only prototype corpus migration map before physical corpus
  reorganization. The map inventories current architecture source guides, ADRs,
  layer rulesets, concern rulesets, and rule packs, maps all 26 YAML
  rules/rule-pack artifacts to proposed numbered corpus packages, and marks
  mixed concerns for split review rather than moving files prematurely.
- Add the reusable `rag-rulebook/rulebook-index/v1` schema and companion guide.
  The index schema represents current prototype paths and proposed corpus
  package paths, catalogs corpora, artifacts, rules, rule packs, chunk
  candidates, graph edges, source references, path mappings, unresolved
  references, diagnostics, and provenance, and advances the next slice to a
  read-only current-state index generator.
- Add a read-only `scripts/02.rag-rulebook/generate-rulebook-index/script.sh`
  command. The generator emits `rag-rulebook/rulebook-index/v1` JSON from the
  current prototype architecture corpus and migration map, resolves
  related/required ruleset edges, extracts rule and rule-pack chunk
  candidates, reports unresolved references, and does not move files, write
  generated artifacts, use embeddings, or call the network.
- Add a read-only `scripts/02.rag-rulebook/validate-rulebook-index/script.sh`
  command. The validator checks generated or saved
  `rag-rulebook/rulebook-index/v1` JSON for required fields, duplicate IDs,
  graph-edge resolution, artifact/rule/rule-pack/chunk/source references,
  path mappings, diagnostics counts, unresolved-reference consistency,
  provenance inputs, and current source path existence before any corpus move.
- Add a read-only `scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh`
  command. The generator validates its source index first, then emits
  `rag-rulebook/chunk-set/v1` JSON by rendering structured
  `chunk_candidates[]` into artifact summary, rule, rule-pack step, and
  required-check chunks with source citations, without arbitrary character
  windows, durable writes, embeddings, network calls, or corpus moves.
- Add a read-only `scripts/02.rag-rulebook/validate-context-packet/script.sh`
  command. The validator checks `rag-rulebook/context-packet/v1` JSON against
  generated `rag-rulebook/chunk-set/v1` chunks, proving selected chunks,
  citations, checks, forbidden actions, stop conditions, budgets, confidence,
  gaps, routing, and provenance resolve before a packet is used as LLM context.
- Add a read-only
  `scripts/02.rag-rulebook/generate-context-packet-fixture/script.sh` command.
  The fixture generator assembles a small deterministic
  `rag-rulebook/context-packet/v1` packet from generated or saved chunks,
  validates it before output, and proves the current index-to-chunks-to-packet
  handoff without claiming to be semantic retrieval.
- Add the retrieval selector policy system as the evolvable instruction layer
  between generated chunks and validated context packets. The system defines a
  policy-pack standard, schema, and seed v1 policy covering prompt,
  chat/session metadata, layer/mode/workflow, focused paths, corpus ownership,
  rule graph expansion, required checks, stop conditions, token budget,
  confidence thresholds, validation handoff, and future semantic recall.
- Add a read-only
  `scripts/02.rag-rulebook/validate-retrieval-policy-pack/script.sh` command.
  The validator checks retrieval-policy-pack YAML for required fields,
  dimensions, precedence ordering, threshold ranges, referenced workflows,
  validators, smoke fixtures, evolution rules, and v1 semantic-recall safety
  before selector runtime code can rely on a policy pack.
- Modularize retrieval policy dimensions while keeping one active policy pack.
  The top-level `policies/retrieval-selector/v1.yml` now acts as the manifest,
  and each imported dimension file owns required inputs, expected actions,
  banned actions, output obligations, gaps/stops, ranking effects, validation
  examples, and allowed change paths so future selector runtime code does not
  invent behavior that belongs in policy.
- Define recognition sources as governed lookup vocabularies owned by
  `02.rag-rulebook`, separate from retrieval chunks. Generated recognition
  sources should come from committed artifacts such as artifact IDs, paths,
  schemas, corpora, layers, workflows, rules, and rule packs; curated sources
  such as action verbs, risk words, aliases, and domain nouns require tighter
  review. Chat may later consume compiled recognition sources opportunistically,
  but must keep its deterministic fallback when `02.rag-rulebook` is absent.


- Decision: Add conditional RAG/rulebook commit gate
  Rationale: When .agentic/02.rag-rulebook exists, the chat before-commit readiness gate now requires scripts/02.rag-rulebook/commit-gates/script.sh. The RAG/rulebook layer owns the validators inside that gate, including the future recognition-source validator once recognition sources exist.


- Decision: Add recognition-source validation before generated sources
  Rationale: The RAG/rulebook layer now has a read-only validate-recognition-sources command. It validates recognition-source YAML for schema shape, plural source_kinds, generated-source provenance, curated-source review triggers, duplicate lookup terms, refresh policy, and term match metadata before generated or curated sources become commit-critical.


- Decision: Generate metadata-backed artifact recognition source
  Rationale: Added recognition.generated.artifacts as the first generated recognition source. It is produced from the existing artifact metadata index, writes exact artifact IDs, file paths, schema names, rule IDs, and rule-pack IDs, and is checked for freshness by the RAG/rulebook commit gate.


- Decision: Generate governed routing recognition source
  Rationale: Extended generate-recognition-sources to generate and freshness-check recognition.generated.routing from governed layer taxonomy, routing policy, retrieval policy corpus/mode definitions, and workflow files. The RAG/rulebook commit gate now checks both generated recognition sources.


- Decision: Add retrieval selector fixture
  Rationale: Added a read-only retrieval selector fixture that validates the active policy pack and recognition sources, matches request/session/focused-path signals against generated lookup sources, constrains candidate chunks by session and prototype bridge corpora, emits a validated context packet, and is now covered by the RAG/rulebook commit gate.


- Decision: Govern evaluation fixtures
  Rationale: Added a harness-wide evaluation fixture standard and a RAG/rulebook retrieval selector evaluation standard so expected outcomes, banned outcomes, validators, ownership, update triggers, gaps, confidence, citations, and token-budget behavior are governed before adding retrieval selector eval cases.


- Decision: Add retrieval selector evaluation suite
  Rationale: Added machine-readable retrieval selector evaluation fixtures for exact RAG/rulebook routing, prompt/session conflict, vague low-confidence prompts, and corpus boundary protection. Added an evaluator command that runs selector packets against expected and banned outcomes, and wired the evaluator into the RAG/rulebook commit gate.


- Decision: Add curated recognition sources
  Rationale: Added curated alias, action, and risk recognition sources so reviewed human-language terms can influence selector prompt recognition without replacing generated repo facts. Updated selector evaluations to prove the spaced RAG rulebook alias and curated action/risk terms are recognized.

## Activity Log

### 2026-06-25T11:12:51Z - Session started

Initial intent: create 02 rag rulebook layer scaffold


### 2026-06-25T11:30:22Z - Commit recorded

Commit: `59d18ed`

Message: Add RAG rulebook layer scaffold

Summary: Added first-class 02.rag-rulebook layer scaffold, routing/classifier coverage, metadata layer renumbering, script-surface docs, and ADR 0022.

ADR impact: ADR 0022 records the new RAG/Rulebook layer and renumbered metadata layers.


### 2026-06-25T11:35:51Z - Commit recorded

Commit: `b61e584`

Message: Plan RAG rulebook service shape

Summary: Added design-only RAG/Rulebook standards for the portable service contract, domain corpus package shape, and ordered repo plan.

ADR impact: No new ADR; this elaborates ADR 0022 within the new RAG/Rulebook layer.


### 2026-06-25T11:54:05Z - Commit recorded

Commit: `222e06d`

Message: Align RAG corpus vocabulary

Summary: Aligned RAG/Rulebook corpus IDs with layer numbering, added the self-corpus, marked service/corpus standards reusable, and deferred the standalone service target name.

ADR impact: No new ADR; elaborates ADR 0022 layer boundaries and the RAG/Rulebook repo plan.


### 2026-06-25T12:47:47Z - Commit recorded

Commit: `88ac5ed`

Message: Add RAG context packet schema

Summary: Added the reusable context-packet v1 schema, linked it from the RAG/Rulebook README and portable service contract, and advanced the repo plan to the rulebook index schema slice.

ADR impact: No new ADR; elaborates ADR 0022 with the first RAG/Rulebook schema artifact.


### 2026-06-25T12:57:05Z - Commit recorded

Commit: `c07901c`

Message: Teach RAG context packet schema

Summary: Added structured field-guide entries to the context-packet schema and a companion human guide explaining packet purpose, field families, good and bad packet shapes, and LLM usage rules.

ADR impact: No new ADR; elaborates ADR 0022 and the context-packet schema slice.


### 2026-06-25T13:04:26Z - Commit recorded

Commit: `29005b5`

Message: Standardize schema artifact guidance

Summary: Promoted the context-packet teachability pattern into the harness artifact standard so new or materially changed schemas include structured field explanations, validation rules where deterministic, companion guides, and schema-guide links.

ADR impact: No new ADR; this is a quality rule in the existing canonical artifact standard.


### 2026-06-25T13:15:45Z - Commit recorded

Commit: `b8c8cf9`

Message: Map prototype corpus migration targets

Summary: Added a read-only prototype corpus migration map covering source guides, ADRs, all 26 current YAML rules/rule-pack artifacts, proposed numbered corpus targets, split-review concerns, reference updates, and validation requirements before any file moves.

ADR impact: No new ADR; this is a planning artifact under the RAG/Rulebook layer and prepares the later index schema and corpus migration.


### 2026-06-25T13:24:32Z - Commit recorded

Commit: `6b2fbb0`

Message: Add RAG rulebook index schema

Summary: Added the reusable rulebook-index v1 schema and companion guide, linked them from the RAG/Rulebook README and repo plan, and advanced the next slice to a read-only current-state index generator.

ADR impact: No new ADR; this schema elaborates ADR 0022 and uses the prototype corpus migration map.


### 2026-06-25T13:50:18Z - Commit recorded

Commit: `258891a`

Message: Add RAG rulebook index generator

Summary: Added the read-only RAG/Rulebook index generator command, smoke test, command docs, schema linkage, and repo-plan status. The generator emits rag-rulebook/rulebook-index/v1 JSON from the current prototype architecture corpus and migration map without moving files, writing generated artifacts, using embeddings, or calling the network.

ADR impact: No new ADR; this implements the read-only generator slice planned under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T13:59:20Z - Commit recorded

Commit: `f3c40a1`

Message: Add RAG rulebook index validator

Summary: Added the read-only rulebook index validator command, smoke test, command docs, schema linkage, and repo-plan status. The validator checks generated or saved rag-rulebook/rulebook-index/v1 JSON for required fields, duplicate IDs, graph-edge resolution, artifact/rule/rule-pack/chunk/source references, path mappings, diagnostics counts, unresolved-reference consistency, provenance inputs, and current source path existence.

ADR impact: No new ADR; this implements the validation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T14:48:45Z - Commit recorded

Commit: `98fefb8`

Message: Add RAG rulebook chunk generator

Summary: Added the read-only rulebook chunk generator command, smoke test, command docs, schema linkage, and repo-plan status. The generator validates its source index first, then emits rag-rulebook/chunk-set/v1 JSON by rendering structured chunk_candidates into artifact summary, rule, rule-pack step, and required-check chunks with citations, without arbitrary character windows, durable writes, embeddings, network calls, or corpus moves.

ADR impact: No new ADR; this implements the chunk generation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T15:04:25Z - Commit recorded

Commit: `7f45e8df92470386ddb125119448ef90ff129439`

Message: Add RAG context packet validator

Summary: Added the read-only context-packet validator command, smoke test, command docs, schema linkage, and repo-plan status. The validator checks rag-rulebook/context-packet/v1 JSON against generated rag-rulebook/chunk-set/v1 chunks so selected chunks, citations, checks, forbidden actions, stop conditions, budgets, confidence, gaps, routing, and provenance resolve before packet use.

ADR impact: No new ADR; this implements the context-packet validation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T15:11:46Z - Commit recorded

Commit: `cd880d067e0e4309e0a823e16eddca0a0d9cc60f`

Message: Add RAG context packet fixture generator

Summary: Added the read-only context-packet fixture generator command, smoke test, command docs, schema linkage, and repo-plan status. The generator assembles a small deterministic rag-rulebook/context-packet/v1 packet from generated or saved chunk sets, validates it before output, and proves the index-to-chunks-to-packet handoff without claiming to be semantic retrieval.

ADR impact: No new ADR; this implements the fixture-builder slice planned under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T18:35:50Z - Commit recorded

Commit: `25d191bde93e3b968650fb22ccb88ec500618e02`

Message: Add RAG retrieval selector policy system

Summary: Added the retrieval selector policy system standard, retrieval-policy-pack schema, seed v1 selector policy pack, layer README links, portable service contract linkage, and repo-plan status. The policy system makes context selection evolvable across prompt, session metadata, layer/mode/workflow, focused paths, corpus ownership, rule graph expansion, required checks, stop conditions, token budget, confidence thresholds, validation handoff, and future semantic recall before runtime selector code is added.

ADR impact: No new ADR; this elaborates ADR 0022 and updates the RAG/Rulebook repo plan before selector implementation.


### 2026-06-25T18:52:53Z - Commit recorded

Commit: `aae2481`

Message: Add RAG retrieval policy validator

Summary: Added the read-only retrieval policy-pack validator command, smoke test, command docs, schema/policy linkage, and repo-plan status. The validator checks retrieval-policy-pack YAML for required fields, required dimensions, per-dimension instruction and validation coverage, precedence ordering, threshold ranges, referenced workflows, validator scripts, smoke fixtures, evolution rules, and v1 semantic-recall safety before selector runtime code can rely on a policy pack.

ADR impact: No new ADR; this implements the policy-pack validation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T19:24:44Z - Commit recorded

Commit: `24b31bb`

Message: Modularize RAG retrieval policy dimensions

Summary: Split the seed retrieval selector policy into one active manifest plus 12 imported dimension files. Added the retrieval-policy-dimension schema and guide, strengthened the policy-pack schema, updated the retrieval policy validator to resolve and validate imported dimensions, and expanded the smoke test to reject missing imports and dimensions without banned actions.

ADR impact: No new ADR; this implements the modular policy-dimension slice under ADR 0022 and the RAG/Rulebook repo plan.


### 2026-06-25T20:13:47Z - Commit recorded

Commit: `b7c91a5`

Message: Define RAG recognition source architecture

Summary: Added the recognition-source system standard and recognition-source schema, updated the prompt retrieval dimension to use governed generated and curated lookup sources, added prompt extraction rules and structured classification outputs, and strengthened the policy-pack validator/smoke test so the prompt dimension must define recognition-source coverage.

ADR impact: No new ADR; this extends the RAG/Rulebook retrieval selector architecture under ADR 0022 and the repo plan before selector runtime implementation.


### 2026-06-25T20:28:44Z - Decision

Decision: Add conditional RAG/rulebook commit gate

Rationale: When .agentic/02.rag-rulebook exists, the chat before-commit readiness gate now requires scripts/02.rag-rulebook/commit-gates/script.sh. The RAG/rulebook layer owns the validators inside that gate, including the future recognition-source validator once recognition sources exist.


### 2026-06-25T20:31:13Z - Commit recorded

Commit: `19af7ab`

Message: Add conditional RAG rulebook commit gate

Summary: Added a RAG/rulebook commit-gates capability and wired the chat before-commit readiness gate to call it whenever .agentic/02.rag-rulebook exists. The layer gate validates the retrieval policy pack now and requires a recognition-source validator once recognition sources are present.

ADR impact: No new ADR; this implements commit-boundary enforcement for the RAG/Rulebook layer under ADR 0022.


### 2026-06-25T20:41:29Z - Decision

Decision: Add recognition-source validation before generated sources

Rationale: The RAG/rulebook layer now has a read-only validate-recognition-sources command. It validates recognition-source YAML for schema shape, plural source_kinds, generated-source provenance, curated-source review triggers, duplicate lookup terms, refresh policy, and term match metadata before generated or curated sources become commit-critical.


### 2026-06-25T20:43:22Z - Commit recorded

Commit: `a3c4da4`

Message: Add recognition source validator

Summary: Added the read-only validate-recognition-sources command, smoke coverage, recognition-source schema alignment to source_kinds, retrieval policy validation linkage, and RAG/rulebook docs and repo-plan updates.

ADR impact: No new ADR; this implements recognition-source validation under ADR 0022 before generated source files are introduced.


### 2026-06-25T20:46:54Z - Decision

Decision: Generate metadata-backed artifact recognition source

Rationale: Added recognition.generated.artifacts as the first generated recognition source. It is produced from the existing artifact metadata index, writes exact artifact IDs, file paths, schema names, rule IDs, and rule-pack IDs, and is checked for freshness by the RAG/rulebook commit gate.


### 2026-06-25T20:54:06Z - Commit recorded

Commit: `f4d6b9d`

Message: Generate artifact recognition source

Summary: Added the first generated recognition source from the artifact metadata index, plus a deterministic generator, smoke test, docs, repo-plan updates, and commit-gate freshness checking for generated recognition sources.

ADR impact: No new ADR; this implements the first metadata-backed recognition-source slice under ADR 0022.


### 2026-06-25T21:08:20Z - Decision

Decision: Generate governed routing recognition source

Rationale: Extended generate-recognition-sources to generate and freshness-check recognition.generated.routing from governed layer taxonomy, routing policy, retrieval policy corpus/mode definitions, and workflow files. The RAG/rulebook commit gate now checks both generated recognition sources.


### 2026-06-25T21:15:41Z - Commit recorded

Commit: `ce34f141705a93a68a7d91eb12350bb5714ee62c`

Message: Generate routing recognition source

Summary: Generated and governed a routing recognition source so RAG/rulebook prompt routing can recognize layer, corpus, mode, and workflow terms from governed sources.

ADR impact: covered by session ADR disposition


### 2026-06-25T21:32:54Z - Decision

Decision: Add retrieval selector fixture

Rationale: Added a read-only retrieval selector fixture that validates the active policy pack and recognition sources, matches request/session/focused-path signals against generated lookup sources, constrains candidate chunks by session and prototype bridge corpora, emits a validated context packet, and is now covered by the RAG/rulebook commit gate.


### 2026-06-25T22:17:00Z - Decision

Decision: Govern evaluation fixtures

Rationale: Added a harness-wide evaluation fixture standard and a RAG/rulebook retrieval selector evaluation standard so expected outcomes, banned outcomes, validators, ownership, update triggers, gaps, confidence, citations, and token-budget behavior are governed before adding retrieval selector eval cases.


### 2026-06-25T22:30:37Z - Commit recorded

Commit: `caf75cc`

Message: Add retrieval selector fixture governance

Summary: Added the first retrieval selector fixture command, wired it into the RAG/rulebook gate, and added harness/RAG standards for governing evaluation fixtures before adding selector eval cases.

ADR impact: covered by session ADR disposition


### 2026-06-25T22:35:51Z - Decision

Decision: Add retrieval selector evaluation suite

Rationale: Added machine-readable retrieval selector evaluation fixtures for exact RAG/rulebook routing, prompt/session conflict, vague low-confidence prompts, and corpus boundary protection. Added an evaluator command that runs selector packets against expected and banned outcomes, and wired the evaluator into the RAG/rulebook commit gate.


### 2026-06-25T22:36:51Z - Commit recorded

Commit: `b0ee2f6`

Message: Add retrieval selector evaluation fixtures

Summary: Added retrieval selector evaluation fixtures and an evaluator command covering exact RAG/rulebook routing, prompt/session conflict, vague low-confidence prompts, and corpus boundary protection. Wired the evaluator into the RAG/rulebook commit gate.

ADR impact: covered by session ADR disposition


### 2026-06-25T22:59:43Z - Decision

Decision: Add curated recognition sources

Rationale: Added curated alias, action, and risk recognition sources so reviewed human-language terms can influence selector prompt recognition without replacing generated repo facts. Updated selector evaluations to prove the spaced RAG rulebook alias and curated action/risk terms are recognized.


### 2026-06-25T23:15:34Z - Commit recorded

Commit: `f84184a`

Message: Add curated recognition sources

Summary: Added governed curated alias, action, and risk recognition sources; wired alias matching into the selector fixture; added selector evaluation coverage for spaced RAG rulebook language and curated action/risk terms.

ADR impact: covered by session ADR disposition

## Commits



- Commit: `59d18ed`
  Time UTC: 2026-06-25T11:30:22Z
  Message: Add RAG rulebook layer scaffold
  Summary: Added first-class 02.rag-rulebook layer scaffold, routing/classifier coverage, metadata layer renumbering, script-surface docs, and ADR 0022.
  ADR impact: ADR 0022 records the new RAG/Rulebook layer and renumbered metadata layers.


- Commit: `b61e584`
  Time UTC: 2026-06-25T11:35:51Z
  Message: Plan RAG rulebook service shape
  Summary: Added design-only RAG/Rulebook standards for the portable service contract, domain corpus package shape, and ordered repo plan.
  ADR impact: No new ADR; this elaborates ADR 0022 within the new RAG/Rulebook layer.


- Commit: `222e06d`
  Time UTC: 2026-06-25T11:54:05Z
  Message: Align RAG corpus vocabulary
  Summary: Aligned RAG/Rulebook corpus IDs with layer numbering, added the self-corpus, marked service/corpus standards reusable, and deferred the standalone service target name.
  ADR impact: No new ADR; elaborates ADR 0022 layer boundaries and the RAG/Rulebook repo plan.


- Commit: `88ac5ed`
  Time UTC: 2026-06-25T12:47:47Z
  Message: Add RAG context packet schema
  Summary: Added the reusable context-packet v1 schema, linked it from the RAG/Rulebook README and portable service contract, and advanced the repo plan to the rulebook index schema slice.
  ADR impact: No new ADR; elaborates ADR 0022 with the first RAG/Rulebook schema artifact.


- Commit: `c07901c`
  Time UTC: 2026-06-25T12:57:05Z
  Message: Teach RAG context packet schema
  Summary: Added structured field-guide entries to the context-packet schema and a companion human guide explaining packet purpose, field families, good and bad packet shapes, and LLM usage rules.
  ADR impact: No new ADR; elaborates ADR 0022 and the context-packet schema slice.


- Commit: `29005b5`
  Time UTC: 2026-06-25T13:04:26Z
  Message: Standardize schema artifact guidance
  Summary: Promoted the context-packet teachability pattern into the harness artifact standard so new or materially changed schemas include structured field explanations, validation rules where deterministic, companion guides, and schema-guide links.
  ADR impact: No new ADR; this is a quality rule in the existing canonical artifact standard.


- Commit: `b8c8cf9`
  Time UTC: 2026-06-25T13:15:45Z
  Message: Map prototype corpus migration targets
  Summary: Added a read-only prototype corpus migration map covering source guides, ADRs, all 26 current YAML rules/rule-pack artifacts, proposed numbered corpus targets, split-review concerns, reference updates, and validation requirements before any file moves.
  ADR impact: No new ADR; this is a planning artifact under the RAG/Rulebook layer and prepares the later index schema and corpus migration.


- Commit: `6b2fbb0`
  Time UTC: 2026-06-25T13:24:32Z
  Message: Add RAG rulebook index schema
  Summary: Added the reusable rulebook-index v1 schema and companion guide, linked them from the RAG/Rulebook README and repo plan, and advanced the next slice to a read-only current-state index generator.
  ADR impact: No new ADR; this schema elaborates ADR 0022 and uses the prototype corpus migration map.


- Commit: `258891a`
  Time UTC: 2026-06-25T13:50:18Z
  Message: Add RAG rulebook index generator
  Summary: Added the read-only RAG/Rulebook index generator command, smoke test, command docs, schema linkage, and repo-plan status. The generator emits rag-rulebook/rulebook-index/v1 JSON from the current prototype architecture corpus and migration map without moving files, writing generated artifacts, using embeddings, or calling the network.
  ADR impact: No new ADR; this implements the read-only generator slice planned under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `f3c40a1`
  Time UTC: 2026-06-25T13:59:20Z
  Message: Add RAG rulebook index validator
  Summary: Added the read-only rulebook index validator command, smoke test, command docs, schema linkage, and repo-plan status. The validator checks generated or saved rag-rulebook/rulebook-index/v1 JSON for required fields, duplicate IDs, graph-edge resolution, artifact/rule/rule-pack/chunk/source references, path mappings, diagnostics counts, unresolved-reference consistency, provenance inputs, and current source path existence.
  ADR impact: No new ADR; this implements the validation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `98fefb8`
  Time UTC: 2026-06-25T14:48:45Z
  Message: Add RAG rulebook chunk generator
  Summary: Added the read-only rulebook chunk generator command, smoke test, command docs, schema linkage, and repo-plan status. The generator validates its source index first, then emits rag-rulebook/chunk-set/v1 JSON by rendering structured chunk_candidates into artifact summary, rule, rule-pack step, and required-check chunks with citations, without arbitrary character windows, durable writes, embeddings, network calls, or corpus moves.
  ADR impact: No new ADR; this implements the chunk generation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `7f45e8df92470386ddb125119448ef90ff129439`
  Time UTC: 2026-06-25T15:04:25Z
  Message: Add RAG context packet validator
  Summary: Added the read-only context-packet validator command, smoke test, command docs, schema linkage, and repo-plan status. The validator checks rag-rulebook/context-packet/v1 JSON against generated rag-rulebook/chunk-set/v1 chunks so selected chunks, citations, checks, forbidden actions, stop conditions, budgets, confidence, gaps, routing, and provenance resolve before packet use.
  ADR impact: No new ADR; this implements the context-packet validation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `cd880d067e0e4309e0a823e16eddca0a0d9cc60f`
  Time UTC: 2026-06-25T15:11:46Z
  Message: Add RAG context packet fixture generator
  Summary: Added the read-only context-packet fixture generator command, smoke test, command docs, schema linkage, and repo-plan status. The generator assembles a small deterministic rag-rulebook/context-packet/v1 packet from generated or saved chunk sets, validates it before output, and proves the index-to-chunks-to-packet handoff without claiming to be semantic retrieval.
  ADR impact: No new ADR; this implements the fixture-builder slice planned under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `25d191bde93e3b968650fb22ccb88ec500618e02`
  Time UTC: 2026-06-25T18:35:50Z
  Message: Add RAG retrieval selector policy system
  Summary: Added the retrieval selector policy system standard, retrieval-policy-pack schema, seed v1 selector policy pack, layer README links, portable service contract linkage, and repo-plan status. The policy system makes context selection evolvable across prompt, session metadata, layer/mode/workflow, focused paths, corpus ownership, rule graph expansion, required checks, stop conditions, token budget, confidence thresholds, validation handoff, and future semantic recall before runtime selector code is added.
  ADR impact: No new ADR; this elaborates ADR 0022 and updates the RAG/Rulebook repo plan before selector implementation.


- Commit: `aae2481`
  Time UTC: 2026-06-25T18:52:53Z
  Message: Add RAG retrieval policy validator
  Summary: Added the read-only retrieval policy-pack validator command, smoke test, command docs, schema/policy linkage, and repo-plan status. The validator checks retrieval-policy-pack YAML for required fields, required dimensions, per-dimension instruction and validation coverage, precedence ordering, threshold ranges, referenced workflows, validator scripts, smoke fixtures, evolution rules, and v1 semantic-recall safety before selector runtime code can rely on a policy pack.
  ADR impact: No new ADR; this implements the policy-pack validation slice planned under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `24b31bb`
  Time UTC: 2026-06-25T19:24:44Z
  Message: Modularize RAG retrieval policy dimensions
  Summary: Split the seed retrieval selector policy into one active manifest plus 12 imported dimension files. Added the retrieval-policy-dimension schema and guide, strengthened the policy-pack schema, updated the retrieval policy validator to resolve and validate imported dimensions, and expanded the smoke test to reject missing imports and dimensions without banned actions.
  ADR impact: No new ADR; this implements the modular policy-dimension slice under ADR 0022 and the RAG/Rulebook repo plan.


- Commit: `b7c91a5`
  Time UTC: 2026-06-25T20:13:47Z
  Message: Define RAG recognition source architecture
  Summary: Added the recognition-source system standard and recognition-source schema, updated the prompt retrieval dimension to use governed generated and curated lookup sources, added prompt extraction rules and structured classification outputs, and strengthened the policy-pack validator/smoke test so the prompt dimension must define recognition-source coverage.
  ADR impact: No new ADR; this extends the RAG/Rulebook retrieval selector architecture under ADR 0022 and the repo plan before selector runtime implementation.


- Commit: `19af7ab`
  Time UTC: 2026-06-25T20:31:13Z
  Message: Add conditional RAG rulebook commit gate
  Summary: Added a RAG/rulebook commit-gates capability and wired the chat before-commit readiness gate to call it whenever .agentic/02.rag-rulebook exists. The layer gate validates the retrieval policy pack now and requires a recognition-source validator once recognition sources are present.
  ADR impact: No new ADR; this implements commit-boundary enforcement for the RAG/Rulebook layer under ADR 0022.


- Commit: `a3c4da4`
  Time UTC: 2026-06-25T20:43:22Z
  Message: Add recognition source validator
  Summary: Added the read-only validate-recognition-sources command, smoke coverage, recognition-source schema alignment to source_kinds, retrieval policy validation linkage, and RAG/rulebook docs and repo-plan updates.
  ADR impact: No new ADR; this implements recognition-source validation under ADR 0022 before generated source files are introduced.


- Commit: `f4d6b9d`
  Time UTC: 2026-06-25T20:54:06Z
  Message: Generate artifact recognition source
  Summary: Added the first generated recognition source from the artifact metadata index, plus a deterministic generator, smoke test, docs, repo-plan updates, and commit-gate freshness checking for generated recognition sources.
  ADR impact: No new ADR; this implements the first metadata-backed recognition-source slice under ADR 0022.


- Commit: `ce34f141705a93a68a7d91eb12350bb5714ee62c`
  Time UTC: 2026-06-25T21:15:41Z
  Message: Generate routing recognition source
  Summary: Generated and governed a routing recognition source so RAG/rulebook prompt routing can recognize layer, corpus, mode, and workflow terms from governed sources.
  ADR impact: covered by session ADR disposition


- Commit: `caf75cc`
  Time UTC: 2026-06-25T22:30:37Z
  Message: Add retrieval selector fixture governance
  Summary: Added the first retrieval selector fixture command, wired it into the RAG/rulebook gate, and added harness/RAG standards for governing evaluation fixtures before adding selector eval cases.
  ADR impact: covered by session ADR disposition


- Commit: `b0ee2f6`
  Time UTC: 2026-06-25T22:36:51Z
  Message: Add retrieval selector evaluation fixtures
  Summary: Added retrieval selector evaluation fixtures and an evaluator command covering exact RAG/rulebook routing, prompt/session conflict, vague low-confidence prompts, and corpus boundary protection. Wired the evaluator into the RAG/rulebook commit gate.
  ADR impact: covered by session ADR disposition


- Commit: `f84184a`
  Time UTC: 2026-06-25T23:15:34Z
  Message: Add curated recognition sources
  Summary: Added governed curated alias, action, and risk recognition sources; wired alias matching into the selector fixture; added selector evaluation coverage for spaced RAG rulebook language and curated action/risk terms.
  ADR impact: covered by session ADR disposition

## Main Refresh Conflicts

- None recorded yet.

## ADR Disposition

ADR needed: yes
ADR path: docs/harness/architecture/adrs/0022-add-rag-rulebook-layer.md
Reason: Adding a first-class agentic layer and renumbering later metadata layers is a durable harness architecture decision.

## Session Metrics

Raised at UTC: 2026-06-25T11:12:51Z
Latest commit at UTC: 2026-06-25T23:15:34Z
Latest commit SHA: f84184a
Chat duration: 43363s (00:12:02:43)
Estimated chat tokens: 3295858 estimated from chat transcript bytes (13183431 bytes; source: Codex session log: /home/owner/.codex/sessions/2026/06/25/rollout-2026-06-25T02-03-04-019efc4d-4c05-7003-b932-f9db433f587e.jsonl)
Estimated chat cost: USD 98.88 estimated from estimated_chat_tokens
Estimated chat cost basis: profile=chat-latest-standard-conservative-output; model=chat-latest; tier=standard; context=standard; rate=USD 30/1M tokens; assumption=all estimated chat tokens are costed at the output-token rate because the transcript-byte metric does not split input, cached input, and output tokens; pricing_snapshot=2026-06-19T00:00:00Z; source=https://developers.openai.com/api/docs/pricing

## Notes

- None recorded yet.
