<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.agents.readme
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: guide
purpose: Index harness review agents and explain when to use single-agent and review-board patterns.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.readme
  path: .agentic/01.harness/README.md
- id: harness.standards.agent-contracts
  path: .agentic/01.harness/standards/agent-contracts.md
-->

# Harness Agents

Harness agents are bounded review roles for planning, research, quality review,
and cross-agent delegation. Use one agent when a task has one clear risk owner.
Use a review board when independent risks need separate owners.

## Agents

- [CFO Token Efficiency](cfo-token-efficiency.md) - reviews token spend,
  comparable-session trends, and safe efficiency delegation.
- [Senior Prompt Engineer](senior-prompt-engineer.md) - reviews prompt
  surfaces, instruction hygiene, determinism, and human learnability.
- [Senior Back-End Architect](senior-backend-architect.md) - reviews backend
  architecture compliance and durable rule gaps.
- [Senior SRE Engineer](senior-sre-engineer.md) - reviews deployment,
  operations, reliability, cloud cost, and runtime safety.
- [SecOps Engineer](secops-engineer.md) - reviews security, secrets, auth,
  exposure, compliance posture, and abuse paths.
- [UX/UI Engineer](ux-ui-engineer.md) - reviews human-facing repo, chat, CLI,
  web, and accessibility experiences.

## Supporting Artifacts

- [Agent Contract Standard](../standards/agent-contracts.md)
- [Harness Agent Use Cases](use-cases.md)
- [Review Agent Scaffold Root Cause Analysis](review-agent-scaffold-root-cause-analysis.md)
- [Run Agent Review Workflow](../workflows/run-agent-review.md)
- [Run Review Board Workflow](../workflows/run-review-board.md)

## Selection Rule

Start with the narrowest responsible agent. Escalate to a review board only
when more than one lane has a blocking decision to make.
