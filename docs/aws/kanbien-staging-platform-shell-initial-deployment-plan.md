<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-initial-deployment
version: 1
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- sre
- security
- architecture
kind: change-plan
purpose: Define the bounded, reversible first AWS deployment plan for the Kanbien staging platform-smoke shell.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Kanbien Staging Platform Shell: Initial Deployment Plan

## Status and boundary

This is a **plan only**. It authorises no AWS mutation. A later execution turn
must name the exact approved resources and follow
`.agentic/aws/workflows/execute-approved-aws-change.md`.

Target context:

- Account/profile: `kanbien-dev` / account `337159794548`
- Region: `eu-west-1`
- Environment: `kanbien/staging`
- Workload: new `kanbien-staging-platform-shell` ECS Fargate server running
  only `apps/platform-smoke`
- Public hostname: `staging.platform.kanbien.com`

This deployment is a platform proof. It must not modify the legacy public
brochure site, `service-platform`, its database/cache, `kanbien.com`,
`www.kanbien.com`, or the separate `rag.kanbien.com` route.

## Current evidence

- The selected ECR repository, machine Cognito client/scope, shared ECS
  cluster, public ALB, hosted zone, and wildcard certificate exist.
- The certificate covers `*.kanbien.com`, including the selected staging host.
- No shell task definition, ECS service, target group, host rule, DNS record,
  log group, alarm, image, or deployed smoke evidence exists.
- Local adapter, target-composition, static infrastructure-policy, rendered
  foundation-template validation, and the real read-only container smoke now
  pass. This proves a local image can start and serve `/livez` and `/readyz`;
  it does not prove an AWS change set or deployed workload.
- The existing ALB has no WAF web ACL. Its current routes serve legacy
  workloads and must not be changed as a side effect of this proof.
- The current repository branch has uncommitted platform work and is ahead of
  `origin/main`. Official deployment images must come from reviewed, pushed
  `origin/main`, never this working tree.

## Defects to correct before an AWS apply

1. The previously incorrect smoke permission and incomplete Cognito task
   environment are corrected in the target profile and service template.
2. The generic in-memory limiter has a tested DynamoDB adapter for this public
   target. The public composition refuses to start without it, the ALB-only
   client-address policy, and reviewed listener limits.
3. Foundation and service CloudFormation templates plus a static policy gate
   exist and passed AWS template validation. No foundation stack or service has
   been created yet.
4. The GitHub workflow now validates templates, publishes an immutable image,
   deploys only the service stack through a dedicated CloudFormation execution
   role, and performs public liveness plus unauthenticated-route smoke. The
   live GitHub role has its older policy and must receive the separately
   reviewed narrowed CloudFormation-policy update before this path can run.
5. A deployed negative-rate-limit test, a WAF/routing proof, and a rollback
   exercise remain absent. The local container-engine smoke now passes, but it
   is not a substitute for those deployed proofs.
6. New resources are consistently tagged `service=platform-shell`, but the
   account has not activated that cost-allocation tag or proven the intended
   tag-scoped monthly budget. This account-level Billing action cannot be
   inferred from an infrastructure template.

## Proposed target design

These choices are proposed for review and must be implemented and tested
locally before the first AWS execution approval.

| Concern | Proposed decision | Why |
| --- | --- | --- |
| Infrastructure definition | Focused CloudFormation source units rendered into one AWS CloudFormation template under `infra/04.deploy/03.product/targets/kanbien/staging/` | The repository keeps ingress, edge protection, IAM, rate limiting, logging, and alerting scanable without changing the single reviewed foundation-stack resource graph. |
| Compute | One 256 CPU / 512 MiB Fargate server task, desired count 1; worker remains at 0 | Proves the server shell at low cost without pretending the in-memory smoke job has a real queue worker. |
| Network | Dedicated service security group: ingress only from the existing ALB security group on TCP 3000; outbound HTTPS only as far as the selected Fargate networking model requires | No direct public inbound path to the task. |
| Routing | New IP target group with `/livez`, dedicated HTTPS listener rule, and Route 53 alias for `staging.platform.kanbien.com` | A host-specific route isolates the proof from legacy root-domain traffic. |
| Authentication | Existing M2M Cognito access-token/JWKS configuration; no client secret delivered to the running service | The service verifies tokens using public keys. The confidential client secret is only for controlled smoke-token acquisition. |
| Shared rate limit | Provider adapter backed by a new DynamoDB fixed-window counter table with TTL and task-role-only `UpdateItem` access | Enforces a shared quota across task replicas without storing raw tokens or a durable personal-data profile. |
| Client address | A target-selected resolver that uses the final ALB-appended `X-Forwarded-For` address only because the task security group admits traffic solely from the ALB | The generic server continues to distrust forwarded headers by default; trust exists only at this reviewed target boundary. |
| Edge protection | New WAFv2 web ACL associated with the existing ALB; every rule is scoped to the new staging host | Gives managed-rule and IP-rate protection before the service while avoiding changes to legacy host behaviour. |
| Observability | ECS `awslogs` delivery of redacted stdout JSON to a 14-day CloudWatch log group; ECS and ALB alarms to a dedicated SNS email topic | Uses a host log facility rather than coupling platform code to CloudWatch. |
| Rollback | ECS deployment circuit breaker with rollback, previous task definition retained, listener rule/DNS only removed through a separate explicit retirement action | A failed new workload does not take over or interrupt an existing host. |

## Required implementation sequence

1. Correct the target metadata and add target-profile validation for the
   declared permission and conditional Cognito configuration.
2. Implement and test the provider-specific DynamoDB rate-limit adapter and
   target-owned trusted-ALB address resolver through the generic platform
   contracts. The generic server must not import AWS SDKs or trust forwarded
   headers by default.
3. Parse the reviewed target transport limits at the target composition root;
   invalid values must prevent process startup.
4. Keep CloudFormation source units focused by responsibility, render them
   deterministically into one foundation template, and run static/policy and
   AWS-template validation for the service security group, task/execution
   roles, DynamoDB table, log group, target group, listener rule, WAF, alarms,
   and SNS topic. Existing ECR, Cognito, ALB, certificate, cluster, and hosted
   zone are inputs, not stack resources to replace.
5. Apply the reviewed IAM inline-policy update that lets GitHub pass only the
   platform-shell service CloudFormation execution role and update only the
   platform-shell service stack. Inspect the live role after the update.
6. Commit, review, and merge the local platform slice. Run the official image
   build from `origin/main`; do not promote a local image.
7. Render the reviewed foundation source units, obtain explicit approval for
   the CloudFormation create/update operation, and only then apply the reviewed
   rendered stack. Inspect the created resources.
8. Run deployed smoke proof: DNS/TLS, public `/livez`, unauthenticated `401`,
   wrong-permission `403`, correctly scoped `200`, `429` from the shared
   limiter, WAF/routing evidence, log delivery, alarm configuration, and a
   rollback exercise.
9. After tagged foundation resources exist, activate the `service` cost
   allocation tag in the account Billing console, wait for billing visibility,
   configure the target-scoped monthly/forecast budget alerts, and record the
   proof. Do not treat a resource tag as a functioning budget by itself.

## Expected AWS blast radius

The first apply creates new, prefix-scoped resources only. The one shared
resource is the existing ALB: it receives a new host-specific listener rule
and a WAF web ACL whose rules are scope-down constrained to
`staging.platform.kanbien.com`. No default action, existing listener rule,
legacy target group, root-domain DNS record, database, cache, or existing ECS
service is replaced.

The WAF association is still a shared-ALB change. Before execution, review the
rendered scope-down statements and listener priority against the live listener
rules. Abort rather than apply if either could affect a legacy hostname.

## Rollback and recovery

- **Bad image or failing task:** ECS deployment circuit breaker restores the
  previous healthy task definition; otherwise update the service to the
  recorded prior task definition and verify `/livez` and target health.
- **Bad new listener route:** remove only the staging-platform listener rule
  after confirming it has no traffic dependency; retain DNS until the route is
  proven unused or a separate approval permits removal.
- **WAF false positive:** change the host-scoped rule to count mode or remove
  only that host-scoped rule after inspection; do not weaken rules for the
  legacy hosts.
- **Rate-limit dependency failure:** fail closed with a controlled `503`, emit
  a safe operational signal, and roll back to the previous known-good task
  definition. Do not silently fall back to the process-local limiter on a
  public target.

## Execution approval checklist

Execution remains blocked until all are true:

- local code, IaC, policy, and target-profile checks pass;
- the exact CloudFormation change set is reviewed;
- the current source is committed and present on `origin/main`;
- immutable image digest, base-image digest, scan, SBOM, and provenance are
  available;
- task and execution IAM roles, WAF scope-down rules, listener priority, and
  SNS subscription are reviewed;
- the user explicitly approves the exact staging stack operation in the
  current chat.
