<!-- agentic-artifact:
owner: harness
kind: prompt
purpose: Reusable prompt for creating one layer architecture ruleset.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/operator-guide.md
-->

# Create Layer Ruleset Prompt

Create one layer ruleset using `.agentic/01.harness/operator-guide.md`,
`.agentic/01.harness/workflows/create-layer-ruleset.workflow.md`, and
`.agentic/01.harness/templates/layer-ruleset.template.yml`.

Use source material from `docs/harness/architecture/guides/markdown`.
Inspect existing layer rules before editing. Preserve source references.
Validate YAML. Print the created path, source refs, assumptions, and validation
result. Stop after this one artifact.
