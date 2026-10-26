<!-- agentic-artifact:
schema: agentic-artifact/v3
id: rag-rulebook.script.validate-okf-source-material-reviews.readme
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
kind: capability-readme
purpose: Explain the governed OKF source-material review validator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.validate-okf-source-material-reviews
  path: scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# Validate OKF Source Material Reviews

`script.sh` validates `rag-rulebook/okf-source-material-review/v1` YAML
records.

The validator makes the OKF review loop deterministic. It rejects accepted
records when required reviewers are missing, scores do not clear the threshold,
blocking gaps remain, or the final decision does not match the recorded review
state. Accepted records bind `source_material.sha256` to
`final_decision.accepted_source_sha256`; both describe the bytes reviewed at
acceptance. A later source edit does not invalidate that historical record's
internal integrity.

The canonical reviewer roles are `architect`, `agentic-engineer`,
`secops-engineer`, and `senior-sre`. Review records cannot reduce or replace
that role set locally.

## Usage

Validate every discovered review record and current-source coverage:

```bash
bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh --current
```

`--current` discovers records under the existing review directory. It validates
all historical records, then requires at least one valid accepted review matching
today's bytes for each referenced source. A stale historical record does not
block a valid successor, and a valid successor never excuses malformed history.
A changed source without a matching accepted review, a missing source, or an
empty review inventory fails. This command does not replace source registration
or the review workflow for a source that has no record yet.

Validate one record against its current source:

```bash
bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh --record <path>
```

`--record` stays strict: a selected historical record whose hash differs from
the current source fails. Use the newly accepted record when authorizing current
source-to-rule derivation; never rewrite an accepted old record to refresh it.

Add `--json` for machine-readable output. Each record reports `integrity_valid`,
`freshness` (`current`, `historical`, or `missing`), recorded/current hashes, and
`current_eligible`. The generated `sources` view reports coverage and the exact
eligible records. These views derive from the existing review records and source
files; there is no separate approval registry.

The smoke test uses disposable Git roots and actual command subprocesses. Its
synthetic scorecards test validation only and do not approve repository source
material. Repository-wide `--current` remains a separate check and continues to
report unrelated missing current reviews.

## Effects

This command is read-only. It does not modify source material, reviewer records,
rules, chunks, or runtime caches.
