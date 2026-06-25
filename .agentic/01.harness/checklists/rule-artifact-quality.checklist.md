<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.checklists.rule-artifact-quality
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: checklist
purpose: Review quality of one architecture rulebook artifact.
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

# Rule Artifact Quality Checklist

- Correct artifact type.
- Correct folder.
- Concise.
- Agent-usable.
- Clear `must` and `must_not`.
- Uses `source_refs`.
- Does not duplicate large guide passages.
- Does not mix task packs with layer rules.
- YAML parses.
