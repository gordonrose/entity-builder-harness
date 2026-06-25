<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.continue-rulebook
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: workflow
purpose: Govern default continuation of architecture rulebook work.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.prompts.next-rulebook-task
  path: .agentic/01.harness/prompts/next-rulebook-task.prompt.md
-->

# Continue Rulebook Workflow

Use this workflow when the user asks to continue architecture rulebook work
without naming a specific artifact type.

<!-- deterministic-check: allow reason="rulebook candidate selection and source-reference coverage require human review; this workflow orders judgment-heavy review rather than replacing it with a deterministic gate" -->
1. Read `.agentic/01.harness/manifest.yml`.
2. Read `.agentic/01.harness/operator-guide.md`.
3. Inspect `.agentic/01.harness/state/rulebook-coverage.yml`.
4. Inspect `.agentic/01.harness/state/rulebook-progress.yml`.
5. Inspect existing rules and rule packs under the canonical paths.
6. Identify the next small artifact.
7. Ask for confirmation if the task is ambiguous.
8. Create or update exactly one artifact unless instructed otherwise.
9. Manually verify each new or changed `source_refs` entry against the named source section.
10. Validate YAML.
11. Update coverage state for the guide content reviewed.
12. Summarize changed paths, assumptions, and validation.
13. Stop.
