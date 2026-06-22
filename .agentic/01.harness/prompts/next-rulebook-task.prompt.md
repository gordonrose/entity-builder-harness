<!-- agentic-artifact:
owner: harness
kind: prompt
purpose: Reusable prompt for recommending the next architecture rulebook task.
domain: architecture-rulebook
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/operator-guide.md
-->

# Next Rulebook Task Prompt

Read `.agentic/01.harness/manifest.yml` and
`.agentic/01.harness/state/rulebook-progress.yml`.

Inspect current rules and rule packs under `docs/harness/architecture/rules`
and `docs/harness/architecture/rule-packs`.

Recommend the next single artifact to create. Include why it should be next,
which source guides appear relevant, and any assumptions. Do not create the
artifact unless asked.
