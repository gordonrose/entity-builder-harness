<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.plan.explanation-aware-chunking-and-retrieval
version: 2
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: plan
purpose: Separate execution-authority retrieval from explanation-support retrieval so source material can teach humans without bloating rule chunks.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
- id: rag-rulebook.script.generate-rulebook-index
  path: scripts/02.rag-rulebook/generate-rulebook-index/script.sh
- id: rag-rulebook.script.generate-rulebook-chunks
  path: scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh
- id: rag-rulebook.policy.retrieval-selector.v1
  path: .agentic/02.rag-rulebook/policies/retrieval-selector/v1.yml
-->
# Explanation-Aware Chunking And Retrieval Plan

## Goal

Make RAG useful for both agent execution and human explanation.

The current local RAG path is strongest for execution: structured rules,
required checks, stop conditions, and compact context packets. That is good,
but it is not enough for questions where the user wants to learn the mental
model, rationale, examples, allowed cases, and disallowed cases.

The target model is:

```txt
source material = rich teaching, rationale, examples, and source claims
rules = compact execution guidance and stop conditions
ADRs = durable decisions and consequences
plans = sequence, milestones, and acceptance criteria
chunks = purpose-tagged retrieval units selected by prompt intent
context packets = selected evidence, not the final human answer
```

## Problem

Detailed source material may be added for learning, but the current generated
chunk set is primarily rule-centric. Broad explanation prompts can retrieve
compact rules while missing the richer source-material sections that were
written specifically to teach the human.

This creates two failure modes:

- rule chunks become bloated with teaching prose because they are the only
  reliable retrieval unit;
- human explanation questions receive terse execution guidance instead of the
  source-backed mental model.

## Direction

Separate chunk purpose from chunk authority.

Chunk purpose answers: "Why might this chunk be selected?"

Authority answers: "What may the consumer do with it?"

Execution prompts should prefer binding rules, checks, stop conditions, and
ADRs. Explanation prompts should prefer source material, guides, ADRs, and
supporting rules. Planning prompts should prefer plans, ADRs, and relevant
rules. Deploy, write, git, and destructive prompts must never treat explanation
chunks as authorization.

## Proposed Chunk Purposes

| Purpose | Source | Primary use |
| --- | --- | --- |
| `rule` | structured YAML rules | Execution guidance, checks, stop conditions |
| `source-explanation` | Markdown source-material sections | Human explanation, mental models, rationale, examples |
| `adr-decision` | ADR sections | Why a decision exists, status, consequences |
| `plan-milestone` | plan sections | Ordered implementation, acceptance criteria, next steps |
| `guide` | guide sections | How to read or use a system/artifact |
| `artifact-summary` | artifact metadata/index | Candidate selection and orientation |
| `retrieval-profile` | generated retrieval profile | Search/ranking hints and artifact roles |

## Proposed Authority Labels

| Authority | Meaning |
| --- | --- |
| `execution-authority` | Binding rule/check/stop material for implementation or operations |
| `explanation-support` | Teaching material; useful for answers, not permission to act |
| `decision-history` | Durable decision context and consequences |
| `implementation-plan` | Sequencing and acceptance guidance |
| `orientation` | Lightweight source identity, ownership, and candidate-selection support |

These labels should be machine-readable in the index, chunk set, and context
packet where relevant.

## Selection Policy

Retrieval should choose different chunk purposes based on prompt intent:

- Implementation or code-change prompts prioritize `rule`,
  `execution-authority`, required checks, stop conditions, and ADRs.
- Explanation, tutor, and "walk me through" prompts prioritize
  `source-explanation`, `guide`, `decision-history`, and supporting rules.
- Planning prompts prioritize `plan-milestone`, `decision-history`, and rules.
- Review prompts prioritize `rule`, tests/checks, source-derived rationale, and
  acceptance criteria.
- Git, deploy, write, and destructive prompts may retrieve explanation chunks
  as background, but authorization still comes only from governed workflows,
  explicit approval, and executable gates.

## Token Budget Policy

Token trimming must respect prompt intent:

- For implementation prompts, trim optional explanation chunks before required
  rules, checks, stop conditions, or citations.
- For explanation prompts, keep the best explanation chunks before lower-value
  implementation details, while preserving any rule chunks needed to avoid
  teaching unsafe or stale guidance.
- For planning prompts, keep plan milestones and acceptance criteria before
  lower-priority background detail.
- Never trim citations required by selected chunks, checks, stops, gaps, or
  forbidden actions.

## Current High-Value Source Material

Start with existing knowledge rather than rewriting everything:

- `docs/harness/architecture/source-material/platform-runtime-enterprise-obligations-v1.md`
  - includes platform runtime shell surfaces and runtime surface boundaries
- `docs/harness/architecture/source-material/platform-infra-capability-layering-v1.md`
  - explains contract/runtime/adapter/infra/environment ownership
- `docs/harness/architecture/source-material/packages-core-contract-surface-v1.md`
  - explains core contract placement and provider-neutral limits
- `docs/04.deploy/source-material/**`
  - explains deploy readiness, AWS, container, and production operations context
- `.agentic/02.rag-rulebook/guides/context-packet.md`
  - explains how humans and agents should read context packets
- `.agentic/02.rag-rulebook/guides/rulebook-index.md`
  - explains generated index and chunk-candidate mental models
- `.agentic/02.rag-rulebook/guides/retrieval-policy-dimension.md`
  - explains retrieval policy dimensions

## Ordered Plan

## Implementation Status

Current status:

- Steps 1-2 are implemented for the first v1 surface: standards, retrieval
  policy dimensions, compiled-policy schema, rulebook-index schema, and
  context-packet schema now distinguish chunk purpose from chunk authority.
- Steps 3-4 are implemented for governed Markdown source-material and guide
  headings: the index generator emits deterministic `source-explanation`
  candidates and the chunk generator renders bounded, cited explanation chunks.
- Steps 5-6 are implemented for deterministic selector fixtures:
  explanation/tutor prompts can select exact-source `source-explanation`
  chunks, side-effecting prompts still require `execution-authority`, and the
  platform runtime source-explanation fixture is registered in source
  projections.
- Step 8 is partially implemented: local runtime freshness fingerprints the
  source-material and guide roots that can produce `source-explanation` chunks.
- Step 7 remains open: a read-only explanation-readiness coverage audit has not
  been added yet.

### 1. Codify The Distinction In Standards

Update RAG/rulebook standards so the source of truth is explicit:

- source material may exist for explanation support, not only rule derivation;
- structured rules remain the binding execution layer;
- context packets carry selected evidence, not final answers;
- explanation chunks cannot authorize side effects.

Candidate files:

- `.agentic/02.rag-rulebook/standards/okf-source-material-quality.md`
- `.agentic/02.rag-rulebook/standards/source-to-rule-derivation.md`
- `.agentic/02.rag-rulebook/standards/retrieval-selector-policy-system.md`

Acceptance:

- Standards define execution-authority vs explanation-support.
- Standards explain when rich source material should be chunked directly.
- Standards state that not all source material should become a YAML rule.

### 2. Extend Schemas

Add machine-readable fields for purpose and authority.

Candidate files:

- `.agentic/02.rag-rulebook/schemas/rulebook-index.schema.yml`
- `.agentic/02.rag-rulebook/schemas/context-packet.schema.yml`
- `.agentic/02.rag-rulebook/schemas/compiled-retrieval-policy.schema.yml`

Acceptance:

- Chunk candidates can carry `chunk_purpose` and `authority`.
- Selected chunks can expose `content_kind`, `chunk_purpose`, and `authority`.
- Schema field guides explain how consumers should use these fields.

### 3. Generate Source Explanation Chunk Candidates

Teach the index generator to emit chunk candidates from governed Markdown
source-material and guide headings.

Candidate files:

- `scripts/02.rag-rulebook/generate-rulebook-index/script.sh`
- `.agentic/02.rag-rulebook/schemas/rulebook-index.schema.yml`

Acceptance:

- Markdown heading sections in approved source-material paths can become
  `source-explanation` candidates.
- Candidate generation is deterministic and read-only.
- Section chunks preserve artifact id, source path, heading path, source ref,
  corpus id, and token estimate.
- The generator does not treat arbitrary Markdown as binding rules.

### 4. Render Source Explanation Chunks

Teach the chunk generator to render those candidates into retrievable chunks.

Candidate files:

- `scripts/02.rag-rulebook/generate-rulebook-chunks/script.sh`
- `scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh`

Acceptance:

- `source-explanation` chunks include heading title, short source context, and
  bounded section content.
- Explanation chunks are cited.
- Existing rule chunks remain unchanged except for added purpose/authority
  metadata.

### 5. Update Retrieval Policy Dimensions

Make intent-aware purpose selection part of governed retrieval policy.

Candidate files:

- `.agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/prompt.yml`
- `.agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/retrieval-strategy.yml`
- `.agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/token-budget.yml`
- `.agentic/02.rag-rulebook/policies/retrieval-selector/v1/dimensions/evidence-bundles.yml`

Acceptance:

- Explanation/tutor prompts boost `source-explanation` and `guide` chunks.
- Implementation prompts boost `rule` and `execution-authority` chunks.
- Token trimming differs by intent.
- Side-effecting prompts cannot be authorized by explanation chunks.

### 6. Add Fixtures

Add selector fixtures that prove explanation-aware behavior.

Candidate fixtures:

- explain platform runtime shell surfaces;
- explain `platform/runtime` vs `platform/server` vs `platform/workers`;
- explain why `app.mount.ts` is the platform boundary;
- implementation prompt for the same surface, proving rules/checks outrank
  explanation chunks;
- deploy/write prompt proving explanation chunks do not authorize execution.

Acceptance:

- Explanation fixtures select at least one `source-explanation` chunk.
- Implementation fixtures select binding rules and checks.
- Side-effect fixtures keep authorization blocked unless workflow/approval
  conditions are met.

### 7. Audit Existing Source Material

Run a read-only coverage report for explanation readiness.

Candidate output:

- source path;
- sections detected;
- likely chunk purpose;
- explanation value;
- execution authority status;
- missing headings or weak section titles;
- recommended repair source: source material, rule, ADR, guide, or plan.

Acceptance:

- The audit distinguishes "not chunked yet" from "not useful for explanation."
- Existing high-value source files are either chunked or listed as gaps.
- No source file is rewritten by the audit.

### 8. Commit Gate And Runtime Freshness

Add freshness checks only after the generated outputs are deterministic and
fixtures prove the behavior.

Acceptance:

- Local runtime freshness accounts for source-explanation chunk inputs.
- Commit gates fail when chunk outputs are stale.
- Hosted/runtime packaging can report explanation chunk counts separately from
  execution-rule chunk counts.

## Stop Conditions

- Explanation chunks are treated as permission to write, commit, deploy, or
  mutate cloud state.
- Source material is chunked without citations or source path provenance.
- The chunker emits unbounded Markdown dumps instead of bounded heading
  sections.
- Token trimming removes required rules/checks/stops from side-effecting
  prompts in order to keep explanation material.
- Source-material body text is treated as a structured rule without a
  source-to-rule derivation.
- Existing high-value source files become invisible because only YAML rules are
  chunked.

## Success Criteria

- Human explanation prompts retrieve source-backed teaching material.
- Implementation prompts still retrieve compact binding rules, checks, and
  stops.
- The context packet tells consumers which selected chunks are binding and
  which are explanatory.
- The platform runtime surface boundary material is retrievable for human
  explanation without stuffing all teaching prose into `platform.yml`.
- Existing source material, ADRs, plans, and guides are accounted for by
  purpose-aware chunking or visible gaps.
