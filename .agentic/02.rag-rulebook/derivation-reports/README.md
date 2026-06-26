<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.derivation-reports.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: capability-readme
purpose: Explain where source-to-rule derivation and drift review reports live.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.standard.source-to-rule-derivation
  path: .agentic/02.rag-rulebook/standards/source-to-rule-derivation.md
- id: rag-rulebook.schema.source-to-rule-derivation-report
  path: .agentic/02.rag-rulebook/schemas/source-to-rule-derivation-report.schema.yml
- id: rag-rulebook.workflow.derive-rules-from-source
  path: .agentic/02.rag-rulebook/workflows/derive-rules-from-source.md
-->
# Source-To-Rule Derivation Reports

This directory stores durable reports for source-material changes that affect
structured rulebook content.

Reports answer:

- what source changed
- which corpus owns the change
- what claims were derived
- what conflicts or drift were found
- what rules, gaps, recognition records, chunks, or evaluations changed
- what checks ran
- what still needs human review

Reports use:

`rag-rulebook/source-to-rule-derivation-report/v1`

Prefer corpus subdirectories such as `04.deploy/` when a report is tied to a
domain corpus.

Do not use reports as source material. Do not use reports as retrieval chunks.
They are governance records for how source becomes rulebook output.
