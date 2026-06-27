<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-retirement-records.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the governed RAG/rulebook retirement-record validator.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.validate-retirement-records
  path: scripts/02.rag-rulebook/validate-retirement-records/script.sh
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# Validate Retirement Records

`script.sh` validates `rag-rulebook/retirement-record/v1` YAML records.

Retirement records make source, rule, and generated artifact removal
auditable. They are for removals, renames, supersessions, and intentionally
retained retired artifacts.

## Usage

Validate the committed retirement directory:

```bash
bash scripts/02.rag-rulebook/validate-retirement-records/script.sh --current
```

Validate one file or directory:

```bash
bash scripts/02.rag-rulebook/validate-retirement-records/script.sh --record <path>
```

Add `--json` for machine-readable output.

## Checks

- required top-level fields
- valid schema, retirement ID, owner layer, corpus ID, status, and review
  decision
- retired artifacts include path, kind, path state, and prior SHA-256 hash
- accepted `removed`, `renamed`, and `superseded` paths no longer exist
- accepted `retained-retired` paths still exist and match the recorded hash
- renamed and superseded artifacts name existing replacement paths
- accepted retirements include checked roots and no remaining active references
- accepted retirements have checks run and no pending checks
- duplicate retirement IDs are rejected

## Effects

This command is read-only. It does not delete files, update references, generate
chunks, or create commits.
