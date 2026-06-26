<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.script.validate-recognition-candidates.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain the recognition-candidate validator command.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.validate-recognition-candidates
  path: scripts/02.rag-rulebook/validate-recognition-candidates/script.sh
- id: rag-rulebook.script.commit-gates
  path: scripts/02.rag-rulebook/commit-gates/script.sh
-->
# Validate Recognition Candidates

`script.sh` validates `rag-rulebook/recognition-candidate/v1` YAML files.

Recognition candidates are review records for important unmatched or ambiguous
prompt terms. This command checks that candidates preserve sentence-level
context, proposed canonical meaning, review state, and safe workflow routing.

## Usage

Validate the committed candidate directory:

```bash
bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh --current
```

Validate a specific file or directory:

```bash
bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh --candidate <path>
```

Add `--json` for machine-readable output.

## Checks

- required top-level fields from the recognition-candidate schema
- valid candidate IDs, statuses, observed sources, and review decisions
- required observed term and sentence
- observed sentence includes the candidate term
- suggested source ID, category, canonical ID, and confidence weight
- optional coverage requirements for candidates whose term needs source
  material before safe retrieval
- staged coverage status for source material, structured rulebook content,
  indexed chunks, and selector evaluation proof
- status and review decision agree
- accepted, merged, rejected, and deferred candidates include required review
  details
- `covered` candidates require every required coverage stage to be present
- `partial` candidates require at least one present and one missing coverage
  stage
- present coverage stages require evidence paths
- duplicate candidate IDs are rejected
- referenced workflow paths exist when supplied

## Commit Gate Behavior

The RAG/rulebook commit gate calls this validator when
`.agentic/02.rag-rulebook/recognition-candidates` exists.

## Effects

This command is read-only. It does not promote candidates, update curated
sources, stage changes, or create commits.
