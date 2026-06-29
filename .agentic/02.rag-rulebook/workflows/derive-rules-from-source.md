<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.workflow.derive-rules-from-source
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern source-material conversion into structured rules with drift and conflict review.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.standard.source-to-rule-derivation
  path: .agentic/02.rag-rulebook/standards/source-to-rule-derivation.md
- id: rag-rulebook.derivation-reports.readme
  path: .agentic/02.rag-rulebook/derivation-reports/README.md
- id: rag-rulebook.workflows.readme
  path: .agentic/02.rag-rulebook/workflows/README.md
-->
# Derive Rules From Source Workflow

Use this workflow when approved source material is created, changed, removed,
or reorganized and the change may affect structured rules, rule packs, indexes,
chunks, selector evaluations, recognition sources, or corpus gaps.

## Required Gates

Follow chat-start, write-location, and current layer workflow gates before
editing files.

If the source material belongs to another corpus owner, keep the source under
that corpus and use this workflow only for the reusable derivation machinery
and report contract.

Before this workflow can accept source material as approved, the source must
have an accepted OKF source-material review record using:

`rag-rulebook/okf-source-material-review/v1`

If the review record is missing, blocked, or still needs revision, stop and use
`review-okf-source-material.md` first.

## Flow

1. Identify changed source material.
2. Confirm the owning corpus and layer.
3. Confirm whether the source state is approved, pending review, or removed.
   For approved source, confirm the accepted OKF review record and reviewer
   scores above 9.5/10.
4. Load existing structured rules, rule packs, corpus gaps, recognition
   candidates, and active selector fixtures that may be affected.
5. Extract the important claims from the source.
6. Compare those claims with existing governed material.
7. Record conflicts, drift, ownership issues, and unresolved decisions.
8. Produce or update a source-to-rule derivation report.
9. Propose the smallest rule, ruleset, recognition, gap, or fixture changes
   needed.
<!-- deterministic-check: allow reason="workflow orders available checks while future derivation tooling decides the exact generated-artifact proof set" -->
10. Run available schema, metadata, index, chunk, and selector checks.
11. Leave generated indexes, chunks, and selector coverage marked pending until
    the relevant generators and evaluations prove them current.

## Stop Conditions

Stop before durable rulebook acceptance when:

- source ownership is unclear
- source approval is missing
- accepted OKF source-material review is missing
- changed source contradicts existing rules
- drift affects existing chunks or fixtures and no update plan exists
- the report cannot identify affected artifacts
- generated indexes or chunks are stale
- selector behavior is unproved for a changed retrieval path
- deploy, git, or destructive execution is implied but not explicitly approved

## Output

The workflow should produce:

- a source-to-rule derivation report
- proposed structured rule changes, when safe
<!-- deterministic-check: allow reason="corpus gap proposal depends on semantic source coverage review until a derivation helper is introduced" -->
- proposed corpus gap updates, when coverage is missing
- proposed selector fixture updates, when retrieval behavior changes
- explicit blocked questions when semantic conflict requires human decision

The report should use:

`rag-rulebook/source-to-rule-derivation-report/v1`
