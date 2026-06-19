# Inspect AWS State Workflow

## Use When

Use this when a request asks to inspect, list, compare, diagnose, verify, or
summarize AWS resources without changing cloud state.

## Required Inputs

- AWS profile or account context
- AWS region, when the service is regional
- target environment, service, or resource family

## Rules

- Run read-only AWS commands only.
- Name the profile, region, and environment in the response.
- Do not print secret values. Secret names, parameter names, ARNs, and resource
  identifiers may be shown when useful.
- Prefer narrow queries over broad dumps.
- If a command would mutate cloud state, stop and switch to
  `execute-approved-aws-change.md` after explicit user approval.

## Output

Summarize the inspected resources, evidence, uncertainty, and recommended next
step. Include command results only at the level needed for the user to make a
decision.
