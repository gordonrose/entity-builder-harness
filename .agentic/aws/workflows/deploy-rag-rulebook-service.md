<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.workflows.deploy-rag-rulebook-service
  version: 1
  status: active
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: workflow
  purpose: Govern GitHub-to-AWS deployment of the RAG/rulebook MCP service.
  portability:
    class: reusable
    targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
  used_by:
  - id: deploy.script.verify-rag-rulebook-deploy-readiness
    path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh
  - id: deploy.rules.02-rag-rulebook.github-to-aws-deployment
    path: docs/04.deploy/rules/02.rag-rulebook/github-to-aws-deployment.yml
  - id: deploy.rules.02-rag-rulebook.deployment-readiness-checks
    path: docs/04.deploy/rules/02.rag-rulebook/deployment-readiness-checks.yml
-->
# Deploy RAG/Rulebook Service

## Use When

Use this workflow when the user explicitly asks to deploy the RAG/rulebook
service or MCP server surface through GitHub and AWS.

This workflow starts in planning mode unless all deploy-readiness proof is
present and the user has explicitly approved deploy execution in the current
chat.

## Required Inputs

- GitHub repository, source policy, deployable ref, exact commit SHA, workflow
  path, workflow name, trigger, target environment, and environment protection
  model
- GitHub OIDC role ARN, audience, subject condition, repository condition,
  ref condition, environment condition, and `id-token` workflow permission
  proof
- immutable service artifact identity and generated corpus package identity
- AWS account, region, runtime family, service target, network boundary, secret
  store, health check, rollback target, and log/metric destinations
- MCP specification version, transport, authentication model, authorization
  boundary, exposed capabilities, audit model, and rate limits
- owner, escalation path, budget, quota, throttling, rollback, and disablement
  evidence

## Required Gate

Before any deploy execution, run:

```bash
bash scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh \
  --manifest <deploy-readiness-manifest.yml> \
  --json
```

The command must return `status: ready`. A blocked report is valid planning
evidence, but it is not deployment approval.

## GitHub Release Path

The GitHub workflow must use a protected deployment environment for staging or
production. Environment secrets and deployment jobs must remain unavailable
until the configured environment protection rules pass.

The workflow must prefer GitHub OIDC to long-lived AWS secrets. The assumed AWS
role must be scoped to the repository, ref or environment, and workflow
boundary, with the exact OIDC condition values recorded before execution.

The workflow must preserve deployment history by recording the workflow run,
commit SHA, artifact digest, corpus package version, target AWS environment,
and deploy result.

## Deployment Phases

1. Validate repo state and RAG/rulebook generated artifacts.
2. Build or select the immutable service artifact.
3. Publish or select the versioned corpus package.
4. Verify artifact provenance and generated corpus provenance.
5. Wait for GitHub environment approval where required.
6. Assume the AWS deployment role through OIDC.
7. Deploy to the selected AWS runtime target.
8. Verify service health, MCP read-only exposure, logs, metrics, and context
   query behavior.
9. Record deployment evidence.

## Rollback

Rollback must name the previous safe runtime target, service artifact, corpus
package, health check, and owner. If rollback cannot name those values, deploy
execution is blocked.

## Disablement

Disablement must include the fastest safe way to stop remote MCP exposure,
disable the GitHub workflow, revoke or narrow the AWS role, and prevent stale
corpus packages from being served.

## Stop Conditions

<!-- deterministic-check: allow reason="readiness verifier enforces executable manifest checks; workflow prose names human-facing stop conditions" -->
Stop before deployment execution when any of these are missing:

- deploy-readiness manifest
- exact remote commit SHA
- GitHub protected environment or equivalent release approval
- source policy and GitHub ref consistency
- OIDC role, audience, and named trust conditions
- immutable artifact and corpus package identity
- AWS account, region, runtime family, and service target
- MCP transport, authentication, authorization, and read-only exposure proof
- budget, quota, rate-limit, and throttling proof
- health check, rollback target, operational owner, or escalation path

## Output

For planning, return the blocked readiness report and the smallest next
governed action.

For approved execution, report the workflow run, commit SHA, artifact identity,
corpus package identity, AWS target, health result, rollback target, and any
remaining follow-up.
