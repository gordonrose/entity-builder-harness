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
