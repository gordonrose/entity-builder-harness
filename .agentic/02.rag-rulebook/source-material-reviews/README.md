<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-material-reviews.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
- sre
kind: review-index
purpose: Define where OKF source-material review records live before source-to-rule derivation.
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
- id: rag-rulebook.standard.okf-source-material-quality
  path: .agentic/02.rag-rulebook/standards/okf-source-material-quality.md
-->
# Source Material Reviews

This directory holds OKF source-material review records.

Use these records before source material is converted into structured YAML
rules, chunks, selector evaluations, corpus packages, or runtime/deploy
instructions.

Review records use:

`rag-rulebook/okf-source-material-review/v1`

Required reviewer roles:

- `architect`
- `agentic-engineer`
- `secops-engineer`
- `senior-sre`

The source material is accepted only when every required reviewer scores it
greater than `9.5/10` and no blocking gaps remain.

Use corpus subdirectories when helpful, for example:

`.agentic/02.rag-rulebook/source-material-reviews/04.deploy/`

Do not use review records as source material. They are audit evidence for the
quality loop. The source material remains under the owning `docs/<layer>/`
corpus path.
