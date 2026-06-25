<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.prompts.review-rule-artifact
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: prompt
purpose: Reusable prompt for reviewing one architecture rulebook artifact.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.operator-guide
  path: .agentic/01.harness/operator-guide.md
-->

# Review Rule Artifact Prompt

Review one existing architecture rulebook artifact using
`.agentic/01.harness/workflows/review-rule-artifact.workflow.md` and the
checklists under `.agentic/01.harness/checklists`.

Check artifact type, folder, source refs, concision, unrelated changes, and YAML
parsing. Report findings first, then assumptions and validation method. Do not
edit unless explicitly asked.
