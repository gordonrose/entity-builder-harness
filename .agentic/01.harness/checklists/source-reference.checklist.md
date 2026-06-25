<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.checklists.source-reference
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: checklist
purpose: Review source references for architecture rulebook artifacts.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.workflows.review-rule-artifact
  path: .agentic/01.harness/workflows/review-rule-artifact.workflow.md
-->

# Source Reference Checklist

- Source docs are from `docs/harness/architecture/guides/markdown`.
- Every major rule has a `source_ref`.
- `source_refs` use doc filenames and section names.
- Do not cite vague "architecture docs" generally.
- If no source is found, mark the assumption clearly.
