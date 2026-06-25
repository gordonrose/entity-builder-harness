<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.prompts.create-rule-pack
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: prompt
purpose: Reusable prompt for creating one task-shaped architecture rule pack.
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

# Create Rule Pack Prompt

Create one task-shaped rule pack using `.agentic/01.harness/operator-guide.md`,
`.agentic/01.harness/workflows/create-rule-pack.workflow.md`, and
`.agentic/01.harness/templates/rule-pack.template.yml`.

Use source material from `docs/harness/architecture/guides/markdown`.
Inspect existing rule packs before editing. Reference layer and concern
rulesets instead of duplicating their contents. Preserve source references.
Validate YAML. Print the created path, source refs, assumptions, and validation
result. Stop after this one artifact.
