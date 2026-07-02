<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.templates.agent-review-report
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: template
purpose: Provide the shared human-readable report shape for harness review agents.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.standards.agent-contracts
  path: .agentic/01.harness/standards/agent-contracts.md
- id: harness.agents.readme
  path: .agentic/01.harness/agents/README.md
-->

# Agent Review Report

## Review Summary

- Agent:
- Agent ID:
- Review mode:
- Task or artifact:
- Decision:
- Overall score:
- Critical blocker present: yes/no
- Confidence:

## Evidence Reviewed

- 

## Findings

### Critical

- None.

### High

- None.

### Medium

- None.

### Low

- None.

## Rubric Scores

| Dimension | Score | Evidence | Notes |
|---|---:|---|---|
|  |  |  |  |

## Delegation Requests

| Target agent | Blocking question | Evidence already reviewed | Needed decision |
|---|---|---|---|
|  |  |  |  |

## Required Follow-Up

- 

## Evidence Gaps

- 

## Reviewer Notes

- Do not average away critical findings.
- Keep implementation recommendations separate from review authority.
- Use the structured scorecard when another workflow, script, or agent will
  consume the result.
