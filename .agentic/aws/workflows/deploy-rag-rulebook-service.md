<!-- agentic-artifact:
  schema: agentic-artifact/v3
  id: aws.workflows.deploy-rag-rulebook-service
  version: 1
  status: active
  created_on: "2026-06-26"
  updated_on: "2026-10-25"
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - agentic
  - sre
  kind: workflow
  purpose: Govern RAG deployment readiness and bounded retirement of the hosted staging service.
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

## Current Hosted Target

The `rag-rulebook-staging` hosted target in account `337159794548`, region
`eu-west-1`, is retired. Harness context retrieval uses `RAG_RULEBOOK_PROVIDER=local`.
The old workflow is an inert tombstone and its deployment manifest is retired.
Do not restore hosted deployment as a fallback for local retrieval failures.
Recommissioning needs a separately reviewed change and explicit approval.

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
- local RAG/runtime build and freshness verification proof
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

For the retired hosted staging target, use the bounded retirement procedure
below. Other targets need a target-specific reviewed disablement plan before
execution.

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


## Hosted Staging Retirement

Use only for the explicitly authorised retirement of `rag-rulebook-staging`
in AWS account `337159794548`, `eu-west-1`, using verified profile `kanbien-dev`.
The [provider applicability clause](../standards/operational-realization-applicability.md#bounded-hosted-rag-retirement)
owns this operation's proof requirements. This procedure does not authorise
any future deployment or unrelated resource change.

### Boundary and evidence

Record the user's approval, account/region, exact resource identifiers, stack
owners, image digests, dependency findings, local-query result and execution
results in the chat log/evidence. Retain existing history. Never retrieve,
print, hash, or copy authentication values into evidence. Read-only AWS CLI,
GitHub API and local configuration inspection may establish the boundary.

Preserve `kanbien-staging`, its ALB/listener, wildcard certificate, VPC/subnets,
DNS hosted zone and account GitHub OIDC provider. Preserve platform-shell,
service-platform, kanbien-core-platform, PostgreSQL, and permission/observability
work. A RAG-named stack is not proof of exclusive ownership.

Before mutations:

1. Verify STS account, region and stack/resource ownership. Inventory service
   and foundation stacks, bootstrap stack, exports/importers, services/tasks,
   task-definition image digests, ECR images, IAM roles, log retention, secret
   metadata, security groups, target groups, DNS and host listener rules.
2. Check repository and available local consumers of `rag.kanbien.com` and
   hosted-provider configuration. Inspect scaling targets, scheduled actions,
   EventBridge rules/Scheduler targets and active GitHub runs for RAG launches.
   Low request counts are not absence-of-consumer proof. An unidentified active
   dependency blocks its affected deletion; continue independent safe work.
3. Set only the provider selection in `~/.config/rag-rulebook/rag.env` to
   `RAG_RULEBOOK_PROVIDER=local`; preserve authentication lines and file access
   mode. Build the local runtime through the existing build command and prove
   a representative context query succeeds with outbound hosted access denied.
   Keep local code, corpus, generated retrieval inputs and retrieval machinery.
4. Disable `.github/workflows/deploy-rag-rulebook-staging.yml` through the
   GitHub workflow disable API; verify no pending/running deployment run can
   race teardown (cancel only runs of that exact dedicated workflow if needed).
   The committed workflow must remain inert with no AWS/OIDC permissions or
   deployment steps. Remove only dedicated RAG deployment variables where
   present; preserve the shared GitHub environment and account OIDC provider.

### Ordered CloudFormation teardown

Use the existing AWS CLI with explicit profile/region and exact discovered
stack/resource identifiers. Before each mutation, reconcile the prior result.
Prepare a non-mutating plan or CloudFormation change set, inspect its exact
resource diff, and execute only the allowlisted scope. Review all parameters
using previous values unless a change is named below. Use the live template
as the base if it differs from repository history; carry only these narrow
changes into it, record that safe diff, and preserve unrelated live properties.
Ephemeral execution helpers must enforce the same account, owner, change-shape
and terminal-state checks; a helper is not permission to broaden scope.

1. Update the foundation stack to add `DeletionPolicy: Retain` and
   `UpdateReplacePolicy: Retain` to `LogGroup` and `ServiceTokenSecret`, and
   `EmptyOnDelete: true` to its dedicated ECR `Repository`. No replacement or
   shared-resource change is allowed. Keep log retention exactly 14 days.
   Record every image digest before authorising repository content deletion.
   Verify the applied template includes these controls. CloudFormation's
   default secret deletion has no recovery window; never use that default.
2. Stop dedicated scheduled/scaling launches, if found and positively owned,
   through their owning stack/configuration. If ownership is uncertain, stop
   the affected mutation. Update only `DesiredCount=0` in the service stack,
   reusing its current template and other parameter values. Wait for stack
   completion and verify desired/running/pending counts are all zero and no
   RAG tasks remain. The repository service template permits only zero tasks.
3. Delete `rag-rulebook-staging-service` through CloudFormation. After deletion,
   verify no service importers of foundation exports remain. An importer
   outside the dedicated service is a stop condition for foundation deletion.
4. Delete `rag-rulebook-staging-foundation` through CloudFormation. Its dedicated
   ECR repository/images, roles, service security group, target group, listener
   host rule and DNS alias are removed by their owner; its log group and token
   secret are retained deliberately. Do not delete shared listener/ALB/zone.
5. Schedule deletion of the retained service-token secret with
   `secretsmanager delete-secret --recovery-window-in-days 30` using the exact
   inventoried ARN; never use force deletion. Record the returned deletion date
   and verify metadata without reading its value. Keep the CloudWatch log group
   with 14-day retention and no new producers.
6. Update the RAG bootstrap stack in place to remove only its dedicated deploy
   role and role output; preserve the shared OIDC provider resource and its
   original physical identity. Add retention protection to the provider.
   <!-- deterministic-check: allow reason="live shared-resource ownership and reviewed change-set approval require operator judgment; execution helpers enforce the recorded allowlist and terminal-state assertions" -->
   Inspect a change set: no provider replacement/deletion or unrelated changes.
   Never delete the bootstrap stack wholesale. Verify the role is absent and
   the provider unchanged. Remove dedicated RAG task-definition revisions
   (deregister active revisions; delete inactive revisions when AWS permits)
   only after confirming no tasks/services/schedules reference them.

### Failure handling and completion

A failed or uncertain API result pauses that operation and its dependants.
Read stack events and resource state before retrying. Record a terminal result
and a new attempt label for a bounded corrected retry within the same reviewed
resource set. A missing resource is success only after verifying its identity
and expected absence; a pending deletion is explicitly reported, not called
complete. Do not force-delete a failed stack, change shared policies, broaden
permissions or improvise a new resource scope. Continue unaffected work and
report the exact dependency or decision when safe completion is blocked.

Verify no dedicated service/tasks/scaling/scheduled targets remain; ECR and
owned dedicated network/access paths are absent; the token is pending scheduled
deletion; logs remain at 14 days; DNS and the hosted route are retired; and the
local context query still passes. Compare protected infrastructure identifiers
and unrelated service desired/running/pending counts with the before inventory.
Run the deploy-readiness smoke test, relevant local retrieval tests and repository
commit gates; integrate only reviewed retirement files through shared git rules.
Report removed, retained and pending resources, recurring costs that stop, and
remaining shared/log costs. Label estimates separately from verified billing.

AWS behavior reviewed 2026-10-25:
[CloudFormation deletion policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-attribute-deletionpolicy.html)
and [ECR EmptyOnDelete](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-ecr-repository.html).
