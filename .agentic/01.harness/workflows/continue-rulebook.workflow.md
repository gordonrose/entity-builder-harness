<!-- agentic-artifact:
owner: harness
kind: workflow
purpose: Govern default continuation of architecture rulebook work.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/prompts/next-rulebook-task.prompt.md
-->

# Continue Rulebook Workflow

Use this workflow when the user asks to continue architecture rulebook work
without naming a specific artifact type.

1. Read `.agentic/01.harness/manifest.yml`.
2. Read `.agentic/01.harness/operator-guide.md`.
3. Inspect `.agentic/01.harness/state/rulebook-progress.yml`.
4. Inspect existing rules and rule packs under the canonical paths.
5. Identify the next small artifact.
6. Ask for confirmation if the task is ambiguous.
7. Create or update exactly one artifact unless instructed otherwise.
8. Validate YAML.
9. Update state only if useful.
10. Summarize changed paths, assumptions, and validation.
11. Stop.
