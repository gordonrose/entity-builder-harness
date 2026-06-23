<!-- agentic-artifact:
owner: harness
kind: workflow
purpose: Govern creation of one task-shaped architecture rule pack.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/prompts/create-rule-pack.prompt.md
-->

# Create Rule Pack Workflow

Use this for task-shaped packs such as add-core-module, create-entity,
add-platform-route, and add-design-system-component.

1. Read the manifest and operator guide.
2. Inspect relevant source guide sections.
3. Inspect existing rule pack examples.
4. Use `templates/rule-pack.template.yml`.
5. Reference layer and concern rulesets in `required_rulesets`.
6. Do not duplicate every rule.
7. Include `applies_when`, `required_rulesets`, `required_checks`,
   `agent_steps`, `must_not`, `success_criteria`, and `source_refs`.
8. Validate YAML.
9. Summarize source refs, assumptions, and final path.
