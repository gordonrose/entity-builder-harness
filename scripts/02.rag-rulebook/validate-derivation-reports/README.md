<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-derivation-reports.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the source-to-rule derivation report validator command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.validate-derivation-reports
  path: scripts/02.rag-rulebook/validate-derivation-reports/script.sh
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# Validate Derivation Reports

`script.sh` validates `rag-rulebook/source-to-rule-derivation-report/v1`
YAML files.

Derivation reports explain how approved source material became structured
rulebook changes, which conflicts or drift were reviewed, and which generated
artifacts still need proof.

## Usage

Validate the committed derivation report directory:

```bash
bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current
```

Validate a specific file or directory:

```bash
bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --report <path>
```

Add `--json` for machine-readable output.

## Checks

- required top-level fields from the derivation-report schema
- valid report schema, report ID, lifecycle status, corpus ID, and owner layer
- changed source paths exist unless the report records removed source material
- source claims include claim IDs, summaries, and evidence paths
- conflict and drift statuses agree with their item lists
- ownership review includes notes
- proposed rule, recognition-candidate, and corpus-gap paths exist when they
  are committed repo paths
- downstream index, chunk, selector, or publish requirements name stale outputs
- validation sections include required checks, check results, and pending checks
- report status and review decision agree
- accepted, blocked, and superseded reports include the required review details
- duplicate report IDs are rejected

## Commit Gate Behavior

The RAG/rulebook commit gate calls this validator when
`.agentic/02.rag-rulebook/derivation-reports` exists.

## Effects

This command is read-only. It does not update rules, generate chunks, publish
corpus packages, or create commits.
