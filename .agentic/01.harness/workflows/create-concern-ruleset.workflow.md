<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.create-concern-ruleset
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern creation of one cross-cutting concern architecture ruleset.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.prompts.create-concern-ruleset
  path: .agentic/01.harness/prompts/create-concern-ruleset.prompt.md
-->

# Create Concern Ruleset Workflow

Use this for cross-cutting concerns such as dependency direction, generated
code, persistence, CI quality, runtime validation, and
security-tenancy-audit.

1. Read the manifest and operator guide.
2. Inspect relevant source guide sections across multiple guides.
3. Inspect existing concern examples.
4. Use `templates/concern-ruleset.template.yml`.
5. Include repo-wide or multi-layer `applies_to.paths`.
6. Keep the concern reusable by multiple rule packs.
7. Validate YAML.
8. Summarize source refs, assumptions, and final path.
