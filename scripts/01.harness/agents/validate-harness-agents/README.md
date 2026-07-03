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
- every score anchor includes dimension-specific evidence, risk, or control
  terms rather than long generic filler
- the semantic rubric validator rejects a built-in shallow negative fixture
- the agent README links every agent
- the rubric README links every rubric
- the use-case matrix names every single-agent and multi-agent expectation
- `fixtures/use-case-fixtures.yml` parses and routes every executable use case
  to the exact expected agent set through the workflow routing tables
- the executable use-case fixtures require evidence, highest-standard
  expectations, failure modes, blocker policy, minimum score policy,
  delegation expectations, board decisions, and review-only authority
- `fixtures/scorecard-fixtures.yml` proves scorecard pass/block/delegate
  semantics and rejects contradictory decisions
- `fixtures/negative-review-fixtures.yml` provides executable negative cases for
  every rubric `negative_fixtures` label
- report and scorecard templates expose required fields and the scorecard
  template parses as JSON-compatible YAML
- invocation workflows expose parseable routing tables, reference templates,
  agents, and blocker handling
- the harness manifest names the full harness-governance scope and does not
  regress to architecture-only or eval-runner-prohibited wording
- the Senior Back-End Architect separates review mode from governed
  implementation mode
- the CFO token-comparison script works against fixture commit logs with
  weighted task/workflow/path/agent similarity and cost/per-query metadata

Run from the repository root:

```bash
bash scripts/01.harness/agents/validate-harness-agents/script.sh
```
