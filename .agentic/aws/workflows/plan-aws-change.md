<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.workflows.plan-aws-change
  version: 1
  status: active
  layer: 03.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: workflow
  purpose: Document Plan AWS Change Workflow.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# Plan AWS Change Workflow

## Use When

Use this when a request asks for an AWS change proposal, migration plan,
deployment target plan, rollback plan, or infrastructure approach before
execution.

## Required Inputs

- AWS profile or account context
- AWS region, when the service is regional
- target environment
- intended resource or service change

## Rules

- Do not change cloud state in this workflow.
- Inspect current state before proposing changes when current state matters.
- Identify blast radius, expected effect, rollback path, and verification
  signal.
- Prefer dry-run, diff, or plan commands where the AWS service or tool supports
  them.
- Ask for explicit approval before switching to execution.

## Output

Provide a concise change plan with target context, current-state evidence,
steps, risks, rollback, and verification.
