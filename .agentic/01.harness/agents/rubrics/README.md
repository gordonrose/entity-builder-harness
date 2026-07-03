<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.agents.rubrics.readme
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: guide
purpose: Index machine-readable professional rubrics for harness review agents.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.professional-review-agent-quality
  path: .agentic/01.harness/standards/professional-review-agent-quality.md
- id: harness.script.agents.validate-harness-agents
  path: scripts/01.harness/agents/validate-harness-agents/script.sh
-->

# Harness Agent Rubrics

These files are the scoring source of truth for harness review agents. They use
JSON-compatible YAML so validators can parse them without external
dependencies.

## Rubrics

- `cfo-token-efficiency.yml`
- `senior-prompt-engineer.yml`
- `senior-backend-architect.yml`
- `senior-sre-engineer.yml`
- `secops-engineer.yml`
- `ux-ui-engineer.yml`
