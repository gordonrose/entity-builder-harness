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
- every agent file points to its machine-readable rubric
- every rubric parses as JSON-compatible YAML
- every rubric includes decision policy, evidence model, delegation model,
  negative fixtures, professional references, and score anchors for `0`
  through `5`
- the semantic rubric validator rejects a built-in shallow negative fixture
- the agent README links every agent
- the rubric README links every rubric
- the use-case matrix names every single-agent and multi-agent expectation
- `fixtures/use-case-fixtures.yml` parses and routes every executable use case
  to the exact expected agent set
- the executable use-case fixtures require evidence, highest-standard
  expectations, failure modes, blocker policy, and review-only authority
- report and scorecard templates expose required fields
- invocation workflows reference templates, agents, and blocker handling
- the CFO token-comparison script works against fixture commit logs

Run from the repository root:

```bash
bash scripts/01.harness/agents/validate-harness-agents/script.sh
```
