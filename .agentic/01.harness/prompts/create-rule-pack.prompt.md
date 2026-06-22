<!-- agentic-artifact:
owner: harness
kind: prompt
purpose: Reusable prompt for creating one task-shaped architecture rule pack.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/operator-guide.md
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
