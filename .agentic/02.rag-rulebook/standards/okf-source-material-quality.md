<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.okf-source-material-quality
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
- sre
kind: standard
purpose: Define the quality bar and iterative review loop for production-grade OKF source material before rule derivation.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.workflow.review-okf-source-material
  path: .agentic/02.rag-rulebook/workflows/review-okf-source-material.md
- id: rag-rulebook.schema.okf-source-material-review
  path: .agentic/02.rag-rulebook/schemas/okf-source-material-review.schema.yml
- id: rag-rulebook.source-material-reviews.readme
  path: .agentic/02.rag-rulebook/source-material-reviews/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# OKF Source Material Quality

## Purpose

Define the quality bar for human-authored Operational Knowledge Framework
source material before it is converted into structured YAML rules, generated
chunks, selector evaluations, corpus packages, or deployable runtime behavior.

The goal is production-grade operating knowledge, not polished prose. Source
material must be readable by humans, precise enough for machines, and complete
enough for an agent to derive deterministic instructions without inventing
missing policy.

## Core Rule

Production source material is not approved until an iterative multi-reviewer
loop scores it above `9.5/10` for every required reviewer role.

Required reviewer roles:

- `architect` - evaluates architecture boundaries, ownership, corpus shape,
  abstraction level, and end-to-end system coherence.
- `agentic-engineer` - evaluates deterministic workflow fit, agent execution
  variables, rule derivation readiness, chunkability, retrieval usefulness,
  token shape, and evaluation coverage.
- `secops-engineer` - evaluates identity, secrets, authorization, abuse paths,
  supply-chain integrity, data exposure, and security-operational controls.
- `senior-sre` - evaluates production safety, GitHub/AWS/deploy rigor,
  observability, reliability, rollback, security, performance, cost, and stop
  conditions.

Each reviewer must produce a scorecard, blocking gaps, recommendations, and a
rerun decision. Recommendations must be applied or explicitly rejected with a
recorded reason before the next loop.

## Required Assessment Dimensions

Every reviewer must assess:

- `coverage` - what the corpus covers and whether the vertical scope is clear.
- `necessity` - why the corpus needs to cover that material.
- `production_grade_gaps` - gaps between the source and a best-in-class,
  production-grade deterministic operating guide for the vertical.
- `execution_variables` - variables an agent or runtime needs to execute the
  instructions flexibly without guessing.
- `human_readability` - whether a human can understand the source, review it,
  and maintain it.
- `machine_readability` - whether the source has explicit sections, stable
  terms, lists, boundaries, stop conditions, and derivation-ready structure.
- `cost_optimization` - whether cost risks, cost controls, and cost tradeoffs
  are explicit.
- `security` - whether secrets, identity, permissions, data exposure, and
  abuse paths are covered.
- `performance` - whether latency, scale, capacity, timeout, resource, and
  degradation expectations are covered.
- `token_optimization` - whether the source can produce compact chunks and
  context packets without losing required meaning.

## Scoring Rules

Use a `0` to `10` score.

`10` means production-grade, best-in-class, near-perfect source material for
the stated vertical.

Above `9.5` means shippable source material with only non-blocking refinements
remaining. A score of exactly `9.5` does not pass because the gate requires
every required reviewer score to be greater than `9.5`.

A reviewer must not score above `9.5` when any of these are true:

- a blocking production gap remains
- a required execution variable is missing
- source ownership or corpus ownership is unclear
- security, rollback, observability, or stop-condition coverage is incomplete
- the material cannot be deterministically converted into structured rules
- the material requires the agent to infer policy that should be explicit
- the material is too verbose to chunk well or too terse to be safe

## Required Loop

1. Draft or update source material.
2. Run an architect review.
3. Run an agentic engineer review.
4. Run a SecOps engineer review.
5. Run a senior SRE review.
6. Record all scores, blocking gaps, recommendations, and reviewer evidence.
7. Apply accepted recommendations to the source material.
8. Record applied changes and rejected recommendations.
9. Rerun all reviewers.
10. Repeat until every reviewer score is greater than `9.5`.
11. Mark the review record `accepted`.
12. Only then use `derive-rules-from-source.md` to convert approved source into
    structured YAML rules and downstream chunks/evaluations.

## Output Requirements

Each loop must produce or update a review record using:

`rag-rulebook/okf-source-material-review/v1`

Review records live under:

`.agentic/02.rag-rulebook/source-material-reviews/`

Use corpus subdirectories when helpful, for example:

`.agentic/02.rag-rulebook/source-material-reviews/04.deploy/`

## Good Actions

- Keep source material canonical and human-authored.
- Make assumptions, variables, boundaries, and non-goals explicit.
- Prefer concrete operating instructions over broad principles.
- Separate universal policy from vertical-specific instructions.
- Preserve reviewer disagreement instead of smoothing it away.
- Convert repeated review recommendations into source structure.
- Treat unresolved security, reliability, cost, or stop-condition gaps as
  blockers.
- Rerun the full reviewer set after changes, not only the reviewer who found a
  gap.

## Banned Actions

Do not:

- derive YAML rules from unapproved source material
- treat a single reviewer score as enough
- average scores to pass the gate
- allow a high score when blocking gaps remain
- skip rereview after recommendations are applied
- use source material as retrieval-ready coverage without structured rules
- hide uncertainty in prose
- let token optimization remove required safety or execution variables
- ask humans to maintain generated hashes manually

## Relationship To RAG

This standard treats the core system as an Operational Knowledge Framework.
RAG is the delivery layer that serves compact context packets from governed
knowledge. Chunking is useful only after the source material is strong enough
to become deterministic rules.
