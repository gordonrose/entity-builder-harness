<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.report-recognition-candidates.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the read-only recognition-candidate review report command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.report-recognition-candidates
  path: scripts/02.rag-rulebook/report-recognition-candidates/script.sh
- id: rag-rulebook.workflow.review-recognition-candidates
  path: .agentic/02.rag-rulebook/workflows/review-recognition-candidates.md
-->
# Report Recognition Candidates

`script.sh` validates recognition-candidate records and then reports their
review state.

The command is a review helper. It does not accept, reject, defer, merge, move,
or mutate candidates.

## Usage

Report the committed candidate directory:

```bash
bash scripts/02.rag-rulebook/report-recognition-candidates/script.sh --current
```

Report a specific candidate file or directory:

```bash
bash scripts/02.rag-rulebook/report-recognition-candidates/script.sh --candidate <path>
```

Add `--json` for machine-readable output.

## Report Contents

The report includes:

- candidate term and observed sentence
- lifecycle directory and status
- review decision
- coverage status and stage counts
- suggested curated source and canonical ID
- review needs
- allowed next actions

## Effects

This command is read-only. It runs the recognition-candidate validator first,
then summarizes valid records.
