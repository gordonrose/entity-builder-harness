<!-- agentic-artifact:
owner: harness
kind: prompt
purpose: Reusable prompt for creating one concern architecture ruleset.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/operator-guide.md
-->

# Create Concern Ruleset Prompt

Create one concern ruleset using `.agentic/01.harness/operator-guide.md`,
`.agentic/01.harness/workflows/create-concern-ruleset.workflow.md`, and
`.agentic/01.harness/templates/concern-ruleset.template.yml`.

Use source material from `docs/harness/architecture/guides/markdown`.
Inspect existing concern rules before editing. Keep the concern reusable across
rule packs. Preserve source references. Validate YAML. Print the created path,
source refs, assumptions, and validation result. Stop after this one artifact.
