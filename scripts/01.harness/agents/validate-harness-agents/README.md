<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.script.agents.validate-harness-agents.readme
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: capability-readme
purpose: Explain the harness review-agent validation script and fixtures.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.script.agents.validate-harness-agents
  path: scripts/01.harness/agents/validate-harness-agents/script.sh
- id: harness.standards.agent-contracts
  path: .agentic/01.harness/standards/agent-contracts.md
-->

# Validate Harness Agents

`script.sh` validates the harness review-agent capability.

It is read-only and covers:

- every required agent file exists
- every agent file has the required contract sections
- the agent README links every agent
- the use-case matrix names every single-agent and multi-agent expectation
- report and scorecard templates expose required fields
- invocation workflows reference templates, agents, and blocker handling
- the CFO token-comparison script works against fixture commit logs

Run from the repository root:

```bash
bash scripts/01.harness/agents/validate-harness-agents/script.sh
```
