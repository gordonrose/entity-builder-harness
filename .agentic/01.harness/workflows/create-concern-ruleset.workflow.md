<!-- agentic-artifact:
owner: harness
kind: workflow
purpose: Govern creation of one cross-cutting concern architecture ruleset.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/prompts/create-concern-ruleset.prompt.md
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
