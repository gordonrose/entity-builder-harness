<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.create-layer-ruleset
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern creation of one layer architecture ruleset.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.prompts.create-layer-ruleset
  path: .agentic/01.harness/prompts/create-layer-ruleset.prompt.md
-->

# Create Layer Ruleset Workflow

Use this for repo layers such as packages-core, platform, apps, design-system,
tools, infra, and harness.

1. Read the manifest and operator guide.
2. Inspect relevant source guide sections.
3. Inspect existing layer examples.
4. Use `templates/layer-ruleset.template.yml`.
5. Include `applies_to.paths`.
6. Include rules with `id`, `title`, `severity`, `summary`, `must`,
   `must_not`, `agent_guidance`, and `source_refs`.
7. Validate YAML.
8. Summarize source refs, assumptions, and final path.
