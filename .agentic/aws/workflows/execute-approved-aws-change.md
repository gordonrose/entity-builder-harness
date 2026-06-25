<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.workflows.execute-approved-aws-change
  version: 1
  status: active
  layer: 03.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: workflow
  purpose: Document Execute Approved AWS Change Workflow.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: repo.agents
    path: AGENTS.md
-->
# Execute Approved AWS Change Workflow

## Use When

Use this only after the user explicitly approves an AWS command or change plan
that may mutate cloud state.

## Required Gates

Before running a mutating command, confirm:

- AWS profile or account context
- AWS region, when the service is regional
- target environment
- exact intended change
- rollback or recovery path

## Rules

- Do not run mutating AWS commands without explicit approval in the current
  chat.
- Use the narrowest command that performs the approved change.
- Do not print or store secret values.
- Stop and ask again before destructive actions such as deleting resources,
  replacing persistent storage, revoking access broadly, or changing DNS in a
  way that could interrupt service.
- Capture the result and verification evidence after execution.

## Output

Report what changed, which profile/region/environment was targeted, whether
verification passed, and any follow-up needed.
