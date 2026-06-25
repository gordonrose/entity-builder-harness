<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.prompts.next-rulebook-task
version: 1
status: active
layer: 01.harness
domain: architecture-rulebook
disciplines:
- agentic
- architecture
kind: prompt
purpose: Reusable prompt for recommending the next architecture rulebook task.
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

# Next Rulebook Task Prompt

Read `.agentic/01.harness/manifest.yml` and
`.agentic/01.harness/state/rulebook-coverage.yml`, then
`.agentic/01.harness/state/rulebook-progress.yml`.

Inspect current rules and rule packs under `docs/harness/architecture/rules`
and `docs/harness/architecture/rule-packs`.

Recommend the next single artifact to create. Include why it should be next,
which source guides appear relevant, and any assumptions. Do not create the
artifact unless asked.
