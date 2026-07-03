<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.run-review-board
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: workflow
purpose: Govern multi-agent review-board composition for harness review agents.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.agents.readme
  path: .agentic/01.harness/agents/README.md
- id: harness.agents.use-cases
  path: .agentic/01.harness/agents/use-cases.md
-->

# Run Review Board

## Purpose

Use this workflow when a task has multiple independent review lanes and each
lane can block the outcome. The board coordinates separate agent reviews; it
does not merge their responsibilities into one general opinion.

## Use When

- `.agentic/01.harness/agents/use-cases.md` names more than one expected agent
- a task touches deployment plus security, architecture, UX, or token spend
- a single-agent review returns `delegate`
- a workflow requests an explicit board decision

## Inputs

- user request or task summary
- changed artifacts, diff, plan, or implementation output
- candidate agents and selection reasons
- evidence packet or source paths for each lane
- board objective and desired terminal decision

## Board Composition

Start with the smallest board that owns all blocking risks. Do not invite every
agent by default.

Use the canonical board routing table below. The validator parses this table
and compares it with executable multi-agent use-case fixtures.

<!-- review-board-routing:start -->
```json
{
  "schema": "harness/review-board-routing/v1",
  "version": 1,
  "boards": [
    {
      "fixture_id": "board.hosted_rag_service_deployment",
      "title": "Hosted RAG Service Deployment",
      "agents": [
        "harness.agents.senior-sre-engineer",
        "harness.agents.secops-engineer",
        "harness.agents.senior-backend-architect",
        "harness.agents.cfo-token-efficiency"
      ],
      "reason": "Hosted RAG service deployment needs deploy control, public exposure security, backend boundary review, and token/per-query cost visibility."
    },
    {
      "fixture_id": "board.harness_workflow_capability_build",
      "title": "Harness Workflow Capability Build",
      "agents": [
        "harness.agents.senior-prompt-engineer",
        "harness.agents.cfo-token-efficiency",
        "harness.agents.ux-ui-engineer"
      ],
      "reason": "Harness workflow capability work needs prompt-surface determinism, comparable token cost review, and a clear human operating path."
    },
    {
      "fixture_id": "board.product_platform_feature_public_ui",
      "title": "Product Platform Feature With Public UI",
      "agents": [
        "harness.agents.senior-backend-architect",
        "harness.agents.ux-ui-engineer",
        "harness.agents.senior-sre-engineer",
        "harness.agents.secops-engineer"
      ],
      "reason": "A product platform feature with a public UI needs backend boundary, user experience/accessibility, deploy, and security review lanes."
    },
    {
      "fixture_id": "board.token_spend_regression_secure_workflow",
      "title": "Token Spend Regression In A Secure Workflow",
      "agents": [
        "harness.agents.cfo-token-efficiency",
        "harness.agents.senior-prompt-engineer",
        "harness.agents.secops-engineer"
      ],
      "reason": "A costly security-sensitive workflow needs token trend review, prompt/context ownership, and security evidence boundaries."
    }
  ]
}
```
<!-- review-board-routing:end -->

For novel work that is not one of the fixture IDs above, compose the smallest
board by applying the risk-signal rules below. A matched rule adds the named
agent only when that lane can independently block the outcome.

<!-- review-board-composition:start -->
```json
{
  "schema": "harness/review-board-composition/v1",
  "version": 1,
  "rules": [
    {
      "id": "token_efficiency_or_budget",
      "agent_id": "harness.agents.cfo-token-efficiency",
      "when_any": [
        "token trend|token spend|token consumption|token efficient",
        "per-query cost|per query cost|retrieval cost|context loading",
        "commitLogs/.*/README\\.md"
      ],
      "blocking_scope": "Token, cost, and comparable-session evidence can block cost or efficiency claims."
    },
    {
      "id": "instruction_surface_or_eval",
      "agent_id": "harness.agents.senior-prompt-engineer",
      "when_any": [
        "\\.agentic/01\\.harness/(workflows|templates|agents|standards|prompts|checklists)/",
        "\\.agentic/[^\\s]+/(skills|evals|evaluations|schemas|orchestrators|prompts|gates|checklists)/",
        "scripts/[^\\s]+/(gates|evaluate|evals?|schemas?)/|scripts/[^\\s]+/(evaluate-|eval-|scorecard|schema)"
      ],
      "blocking_scope": "Prompt, workflow, schema, gate, skill, eval, and learnability defects can block harness instruction quality."
    },
    {
      "id": "backend_architecture_boundary",
      "agent_id": "harness.agents.senior-backend-architect",
      "when_any": [
        "backend|architecture|platform capability|entity|feature|capability boundary|dependency",
        "src/platform/",
        "docs/harness/architecture/"
      ],
      "blocking_scope": "Backend boundary, dependency-direction, and durable architecture-rule gaps can block the work."
    },
    {
      "id": "deployment_runtime_reliability",
      "agent_id": "harness.agents.senior-sre-engineer",
      "when_any": [
        "deployment|deploy workflow|github actions|runtime|rollback|observability",
        "aws|ecs|ecr|rds|route53|cloudwatch|hosted service",
        "\\.github/workflows/"
      ],
      "blocking_scope": "Deploy control, rollback, observability, runtime reliability, and cloud cost can block release readiness."
    },
    {
      "id": "security_trust_boundary",
      "agent_id": "harness.agents.secops-engineer",
      "when_any": [
        "security|public|semi-public|exposes?|secret|credential|authentication|authorization|auth",
        "least privilege|owasp|iso|trust boundary|audit logging|rate limiting",
        "security-sensitive"
      ],
      "blocking_scope": "Security controls, secrets, auth, abuse, audit, and trust-boundary findings can block the work."
    },
    {
      "id": "human_facing_interface",
      "agent_id": "harness.agents.ux-ui-engineer",
      "when_any": [
        "chat or cli|cli|blocked response|fallback|terminal output|human operator",
        "user-facing|web ui|frontend|design-system|wcag|persona|accessibility",
        "clear to a human operator"
      ],
      "blocking_scope": "Human-facing repo, CLI, chat, web, and accessibility defects can block usability or operator safety."
    }
  ]
}
```
<!-- review-board-composition:end -->

## Procedure

1. State the board objective and selected agents.
2. Give each agent only the evidence required for its lane.
3. Run each agent through `run-agent-review.md`.
4. Collect scorecards and reports without averaging away blockers.
5. Name cross-agent conflicts and the decision owner for each conflict.
6. Return the board decision after every blocking lane is resolved or explicitly
   recorded as blocked.

## Board Decision Rules

- `pass`: every participating agent returns `pass`.
- `pass_with_notes`: no participating agent blocks, and at least one returns
  `pass_with_notes`.
- `block`: any participating agent returns `block`.
- `delegate`: any required lane still needs another agent decision.
- `not_applicable`: the board evidence shows multi-agent review is not needed.

Critical findings block the board even when the average score is high.

## Outputs

- board objective
- selected agents and reasons
- per-agent scorecards
- cross-agent conflicts
- board decision
- required follow-up

## Stop Conditions

Stop when a required lane lacks evidence, an agent cannot be selected from the
contracted set, governance coverage is absent, or the board would need
implementation authority rather than review authority.

## Completion

The board is complete when it returns a terminal decision with all participating
agent scorecards attached or referenced.
