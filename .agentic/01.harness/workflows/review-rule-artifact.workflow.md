<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.review-rule-artifact
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern review of one architecture rulebook artifact.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.prompts.review-rule-artifact
  path: .agentic/01.harness/prompts/review-rule-artifact.prompt.md
-->

# Review Rule Artifact Workflow

Use this to review one existing layer ruleset, concern ruleset, or rule pack.

Check that:

- The artifact is in the correct folder.
- The artifact is the right type: layer, concern, or task pack.
- `source_refs` are present.
- No unrelated files changed.
- YAML parses.
- The artifact is concise enough for future agent use.
