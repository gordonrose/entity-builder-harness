<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.prompts.create-concern-ruleset
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: prompt
purpose: Reusable prompt for creating one concern architecture ruleset.
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

# Create Concern Ruleset Prompt

Create one concern ruleset using `.agentic/01.harness/operator-guide.md`,
`.agentic/01.harness/workflows/create-concern-ruleset.workflow.md`, and
`.agentic/01.harness/templates/concern-ruleset.template.yml`.

Use source material from `docs/harness/architecture/guides/markdown`.
Inspect existing concern rules before editing. Keep the concern reusable across
rule packs. Preserve source references. Validate YAML. Print the created path,
source refs, assumptions, and validation result. Stop after this one artifact.
