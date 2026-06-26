<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.recognition-candidates.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: index
purpose: Define the durable recognition-candidate review inbox layout.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.recognition-candidate
  path: .agentic/02.rag-rulebook/schemas/recognition-candidate.schema.yml
- id: rag-rulebook.workflow.review-recognition-candidates
  path: .agentic/02.rag-rulebook/workflows/review-recognition-candidates.md
- id: rag-rulebook.script.validate-recognition-candidates
  path: scripts/02.rag-rulebook/validate-recognition-candidates/script.sh
-->
# Recognition Candidates

This directory is the durable review inbox for important prompt terms that are
not yet covered by generated or curated recognition sources.

Runtime recognition may observe candidates, but it must not automatically add
curated terms.

Use:

- `inbox/` for candidates awaiting review
- `accepted/` for candidates that became curated-source terms
- `rejected/` for candidates reviewed and rejected
- `deferred/` for candidates waiting for more evidence

Candidate records must follow
`schemas/recognition-candidate.schema.yml` and preserve the sentence where the
term appeared.

Validate committed candidate records with:

```bash
bash scripts/02.rag-rulebook/validate-recognition-candidates/script.sh --current
```
