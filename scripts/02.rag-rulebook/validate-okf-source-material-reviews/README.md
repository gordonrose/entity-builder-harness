<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-okf-source-material-reviews.readme
version: 1
status: active
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
blocking gaps remain, source hashes are stale, or the final decision does not
match the recorded review state.

The canonical reviewer roles are `architect`, `agentic-engineer`,
`secops-engineer`, and `senior-sre`. Review records cannot reduce or replace
that role set locally.

## Usage

Validate all current review records:

```bash
bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh --current
```

Validate one record:

```bash
bash scripts/02.rag-rulebook/validate-okf-source-material-reviews/script.sh --record <path>
```

Add `--json` for machine-readable output.

## Effects

This command is read-only. It does not modify source material, reviewer records,
rules, chunks, or runtime caches.
