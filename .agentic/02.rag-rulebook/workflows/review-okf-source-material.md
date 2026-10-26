<!-- agentic-artifact:
schema: agentic-artifact/v3
id: rag-rulebook.workflow.review-okf-source-material
version: 2
status: active
created_on: "2026-06-29"
updated_on: "2026-10-26"
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
- sre
kind: workflow
purpose: Govern iterative multi-reviewer approval of OKF source material before source-to-rule derivation.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.standard.okf-source-material-quality
  path: .agentic/02.rag-rulebook/standards/okf-source-material-quality.md
- id: rag-rulebook.workflows.readme
  path: .agentic/02.rag-rulebook/workflows/README.md
- id: rag-rulebook.workflow.derive-rules-from-source
  path: .agentic/02.rag-rulebook/workflows/derive-rules-from-source.md
-->
# Review OKF Source Material Workflow

Use this workflow when source material is created or materially changed for an
Operational Knowledge Framework corpus and the material is expected to become
structured rules, chunks, selector evaluations, corpus packages, or deployable
runtime guidance.

## Required Gates

Follow chat-start, write-location, and current layer workflow gates before
editing files.

If the source belongs to another corpus owner, keep the source under that
corpus and use this workflow only for the review loop and review record.

Do not derive structured YAML rules until the source material has an accepted
review record with every required reviewer score greater than `9.5`.

## Required Reviewers

Run the loop with these reviewer roles:

- `architect`
- `agentic-engineer`
- `secops-engineer`
- `senior-sre`

Each reviewer must independently assess the same source material and produce a
scorecard. The loop passes only when all reviewers score above `9.5/10`.

## Review Dimensions

Each reviewer must address:

1. What the corpus is covering.
2. Why the corpus needs to cover it.
3. Gaps between current corpus content and a best-in-class, production-grade,
   deterministic instruction set for the vertical.
4. Variables required to execute the instructions flexibly.
5. Human readability.
6. Machine readability.
7. Cost optimization.
8. Security.
9. Performance.
10. Token optimization.

## Flow

1. Identify the source material path, corpus ID, vertical, and target user.
2. Confirm the source is non-executable unless explicitly governed otherwise.
3. Create or update a pending review record under
   `.agentic/02.rag-rulebook/source-material-reviews/`. Preserve accepted records
   unchanged. A source revision after acceptance receives a new review ID and
   record path; historical scores and accepted hashes remain attached to the
   bytes originally reviewed.
4. Run the architect review and record score, gaps, and recommendations.
5. Run the agentic engineer review and record score, gaps, and
   recommendations.
6. Run the SecOps engineer review and record score, gaps, and recommendations.
7. Run the senior SRE review and record score, gaps, and recommendations.
8. Summarize cross-review agreement, disagreement, blockers, and recommended
   changes.
9. Apply accepted recommendations to the source material.
10. Record applied changes and rejected recommendations with reasons.
11. Rerun all reviewers.
12. Repeat until every reviewer score is greater than `9.5`.
13. Mark the new review record `accepted`, recording the same generated source
    SHA-256 in `source_material.sha256` and
    `final_decision.accepted_source_sha256`.
14. Run `bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh
    --record <new-record-path>` before current source-to-rule derivation.
    `--current` separately validates all historical record integrity and requires
    a matching valid accepted review for each referenced current source. A stale
    historical record is retained evidence, not approval for changed bytes.
15. Continue to `derive-rules-from-source.md`.

## Stop Conditions

Stop before acceptance when:

- any reviewer scores `9.5` or lower
- any reviewer records a blocking gap
- source ownership or corpus ownership is unclear
- security, reliability, rollback, observability, cost, or performance
  requirements are unclear
- execution variables are missing
- the source cannot be converted into deterministic structured rules
- reviewer recommendations conflict and no resolution is recorded
- changes were applied but not rereviewed by all roles

## Output

The workflow should produce:

- one `rag-rulebook/okf-source-material-review/v1` review record
- updated source material, when recommendations are accepted
- a clear accepted, needs-revision, or blocked state
- a handoff to `derive-rules-from-source.md` only after acceptance

The review record should preserve scores, blocker state, reviewer findings,
recommendations, applied changes, rejected recommendations, and validation
evidence.
