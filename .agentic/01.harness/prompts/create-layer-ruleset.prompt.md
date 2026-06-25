<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.prompts.create-layer-ruleset
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: prompt
purpose: Reusable prompt for creating one layer architecture ruleset.
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

# Create Layer Ruleset Prompt

Create one layer ruleset using `.agentic/01.harness/operator-guide.md`,
`.agentic/01.harness/workflows/create-layer-ruleset.workflow.md`, and
`.agentic/01.harness/templates/layer-ruleset.template.yml`.

Use source material from `docs/harness/architecture/guides/markdown`.
Inspect existing layer rules before editing. Preserve source references.
Validate YAML. Print the created path, source refs, assumptions, and validation
result. Stop after this one artifact.
