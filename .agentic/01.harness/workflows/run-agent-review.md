<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.run-agent-review
version: 1
status: active
layer: 01.harness
domain: governance.agents
disciplines:
- agentic
kind: workflow
purpose: Govern single-agent review invocation for harness review agents.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.agents.readme
  path: .agentic/01.harness/agents/README.md
- id: harness.standards.agent-contracts
  path: .agentic/01.harness/standards/agent-contracts.md
-->

# Run Agent Review

## Purpose

Use this workflow to invoke one harness review agent for a bounded review,
planning, or research output. Prefer this workflow over a review board when one
agent clearly owns the primary risk.

## Use When

- a task maps to one review lane in `.agentic/01.harness/agents/use-cases.md`
- a workflow, skill, template, schema, gate, or implementation output needs one
  specialist review
- another workflow requests a specific agent decision

## Inputs

- user request or task summary
- target artifact, diff, plan, implementation output, or command output
- selected agent path
- relevant source-of-truth workflow, standard, rule, or context packet
- desired review mode: `review`, `planning`, or `research`

## Agent Selection

Select the narrowest responsible agent from the canonical routing table below.
The validator parses this table and runs the executable use-case fixtures
against it; do not duplicate a separate prose-only routing table elsewhere.

<!-- review-agent-routing:start -->
```json
{
  "schema": "harness/review-agent-routing/v1",
  "version": 1,
  "routes": [
    {
      "agent_id": "harness.agents.cfo-token-efficiency",
      "reason": "token trend, token efficiency, retrieval cost, context-loading waste, or per-query cost",
      "match_patterns": [
        "estimated chat token",
        "token trend|token spend|token consumption|token efficient|token and per-query cost",
        "retrieval-policy|broad corpora|context loading",
        "cost visibility|per-query cost|per query cost"
      ]
    },
    {
      "agent_id": "harness.agents.senior-prompt-engineer",
      "reason": "prompt surface, instruction hygiene, deterministic boundary, source-of-truth ownership, or human learnability of harness instructions",
      "match_patterns": [
        "llm|instructions|instruction surface|prompt surface",
        "workflow, skill, gate, template, schema, orchestrator, or agent",
        "\\.agentic/01\\.harness/(workflows|templates|agents)/",
        "deterministic|source-of-truth|onboarding|context loading|review-board invocation"
      ]
    },
    {
      "agent_id": "harness.agents.senior-backend-architect",
      "reason": "backend architecture, platform/app/entity/feature/capability boundary, dependency direction, or durable architecture rule gap",
      "match_patterns": [
        "backend|architecture|platform capability|entity|feature|capability boundary|rulebook gap",
        "docs/harness/architecture/",
        "src/platform/"
      ]
    },
    {
      "agent_id": "harness.agents.senior-sre-engineer",
      "reason": "deployment, runtime, reliability, rollback, observability, AWS/GitHub Actions, or cloud cost",
      "match_patterns": [
        "deployment|deploy workflow|github actions|runtime|rollback|observability|service-choice",
        "aws deployment|aws runtime|\\b(ecs|ecr|rds|route53|cloudwatch)\\b",
        "hosted service becomes more expensive per query|infrastructure scaling|runtime logging|cloud caching"
      ]
    },
    {
      "agent_id": "harness.agents.secops-engineer",
      "reason": "security, secrets, authn/authz, public exposure, least privilege, abuse, audit, OWASP, ISO, or trust boundary",
      "match_patterns": [
        "security|public|semi-public|exposes?|secret|credential|authentication|authorization|auth",
        "least privilege|owasp|iso|trust boundary|audit logging|rate limiting",
        "security-sensitive"
      ]
    },
    {
      "agent_id": "harness.agents.ux-ui-engineer",
      "reason": "human-facing repo, chat, CLI, web, frontend, persona, accessibility, WCAG, recovery, or operator experience",
      "match_patterns": [
        "chat or cli|cli|blocked response|fallback|terminal output|human operator",
        "user-facing|web ui|frontend|design-system|wcag|persona|accessibility",
        "clear to a human operator"
      ]
    }
  ]
}
```
<!-- review-agent-routing:end -->

Use `.agentic/01.harness/agents/use-cases.md` as the first test fixture source
when the correct agent is unclear.

## Procedure

1. State the selected agent, review mode, and reason for selection.
2. Load the selected agent file and the agent contract standard.
3. Gather the smallest sufficient evidence set named by the agent.
4. Run deterministic checks or metric scripts named by the current workflow
   before asking the agent to interpret results.
5. Produce `templates/agent-review-report.md` output for humans.
6. Produce `templates/agent-scorecard.yml` output when another workflow, script,
   or agent may consume the result.
7. Treat `block` and `delegate` decisions as unfinished review states until the
   blocker or delegation is resolved.

## Outputs

- selected agent and selection reason
- evidence reviewed
- agent review report
- scorecard, when required
- decision
- delegation request, when required

## Stop Conditions

Stop when evidence is absent, the selected agent returns `not_applicable`, the
task needs a review board, governance coverage is absent, or the requested
action exceeds reviewer authority.

## Completion

The review is complete when the selected agent returns `pass` or
`pass_with_notes`, or when the workflow records a `block`, `delegate`, or
`not_applicable` result as the intended terminal output for the current task.
