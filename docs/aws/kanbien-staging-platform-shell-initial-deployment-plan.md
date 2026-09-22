<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.plan.kanbien-staging-platform-shell-initial-deployment
version: 17
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
  cluster, public ALB, hosted zone, and existing wildcard certificate exist.
- The foundation stack was created from the reviewed
  `foundation-initial-20260906-1915` change set. It created the target group,
  host rule, DNS alias, WAF, rate-limit table, log group, alarms, alert topic,
  and workload roles.
- The existing default certificate covers `*.kanbien.com`, which matches one
  label such as `staging.kanbien.com`, but it does **not** cover the two-label
  host `staging.platform.kanbien.com`. The approved repair is complete: the
  foundation owns an `ISSUED` DNS-validated ACM certificate for
  `platform.kanbien.com` and `*.platform.kanbien.com`, attached as a
  non-default SNI certificate without replacing the shared listener's default
  certificate. An external client now verifies the staging hostname.
- The `public-tls-repair-main-20260906-2212` change set was recreated from
  pushed `origin/main`, reviewed with exactly two additions and no replacement
  or modification, then executed successfully. The foundation stack is
  `UPDATE_COMPLETE`.
- Local adapter, target-composition, static infrastructure-policy, rendered
  foundation-template validation, and the real read-only container smoke now
  pass. This proves a local image can start and serve `/livez` and `/readyz`;
  it does not prove an AWS change set or deployed workload.
- The shared ALB serves legacy workloads and has the foundation WAF associated
  with host-scoped rules for this platform hostname only. Its existing routes
  and default certificate remain unchanged.
- The deployed platform-shell baseline source was committed and present on
  `origin/main`. The prepared observability update is local source until it is
  reviewed, committed, and merged. Official deployment images must come from
  reviewed, pushed `origin/main`, never a local working tree.
- The first remote-main GitHub workflow attempt built and pushed an immutable
  platform-shell image but stopped before any service-stack mutation. ECR
  created its scan record asynchronously after the workflow's original waiter
  had already exited; the completed scan then reported 4 critical and 15 high
  findings. The scan policy correctly rejected that image. The account-level
  ECR Basic scan-on-push rule is now explicitly configured for all current
  repositories, and the workflow now waits separately for record creation.
  The next image uses a minimal, non-root Distroless Node runtime rather than
  shipping the general-purpose Debian runtime layer.
- On 2026-09-07, workflow run `34123406369` deployed source commit
  `c9aac48ebaa3f9ca0ee8c193391b26aa60913e01`. The immutable image digest is
  `sha256:f73459a3c7a52616fbad11954f03b8e011f723408a555b2d3c8bc9875b32c9d4`.
  Its ECR scan completed with zero critical and zero high findings; SBOM and
  provenance attestations were created before the service stack deployment.
  CloudFormation completed successfully, and both the workflow and an
  independent client verified TLS, `/livez` = `200`, and an unauthenticated
  protected route = `401`.
- Before the 2026-09-22 observability update, the live target had two `OK` ALB
  alarms, a confirmed SNS email subscription, a 14-day log group with a recent
  stream event, and one desired plus one running platform-shell task. The
  follow-up added the three service alarms (running-count mismatch, high CPU,
  and high memory) through a separately reviewed change set.
- On 2026-09-22, the reviewed observability foundation and service change sets
  were applied. The cluster now has enhanced Container Insights; the three ECS
  alarms and the two ALB alarms are `OK`; both stacks are `UPDATE_COMPLETE`;
  and the service runs revision 2 with the task-local collector.
- The immutable revision-2 image was scan-accepted with zero critical and high
  findings. A controlled protected request returned `200`, and CloudWatch
  PromQL returned its outcome counter and latency histogram. This proves metric
  delivery, not the 28-day SLO, exporter-loss coverage, or alert delivery.

## Remaining verification work

1. The governed controlled-token smoke command and temporary GitHub Actions
   scheduler are active on `origin/main`. Its separate OIDC role can only read
   the one declared opaque raw client secret,
   then make the fixed HTTPS `GET` smoke route with an in-memory token and
   status-only output. Its nominal `17 */4 * * *` UTC cadence is best effort:
   GitHub scheduling delay or a missed run must become a coverage concern, not
   a false green SLO. The separately reviewed IAM role/policy is deployed and
   verified; the workflow is on `origin/main`; and a manual first redacted
   `200` result is recorded. The first clock-triggered run remains to be
   observed. It is labelled synthetic boundary evidence, never unqualified
   customer SLO traffic, and will later be replaced by the governed platform
   scheduler module and adapter.
2. Create a separate, deliberately scope-less or differently scoped Cognito
   machine client before proving the protected route returns `403`. Keep the
   existing correctly scoped `200` proof separate; an invalid token is a `401`
   test, not an authorization proof. Store any additional secret outside the
   repository and record only safe status results.
3. Prove the shared limit with at most the target's declared limit plus one
   sequential request, stopping on the first `429`. Inspect the ALB host rule
   and WAF association read-only, then perform a bounded hostname/routing
   check. Do not use a broad load test or malicious WAF payload as evidence.
4. Implement the target-owned metric-freshness/coverage signal before
   performing a separately approved exporter-loss rehearsal. The detailed
   boundary, safety controls, and evidence requirements are in the
   [exporter-loss rehearsal plan](kanbien-staging-platform-shell-exporter-loss-rehearsal-plan.md).
   It uses a disposable staging task revision whose application exporter has an
   intentionally unavailable loopback endpoint; the protected request must
   still work while the external coverage check reports incomplete SLO
   confidence and reaches its alert destination. Restore the normal revision
   immediately through the recorded rollback path.
5. Prove redacted log delivery, explicitly marked alarm receipt, and a
   reversible task-definition rollback rehearsal. A successful deployment or
   an alarm merely showing `OK` is not either proof.
6. New resources are consistently tagged `service=platform-shell`, but the
   account has not activated that cost-allocation tag or proven the intended
   tag-scoped monthly budget. This account-level Billing action cannot be
   inferred from an infrastructure template.

## Temporary synthetic scheduler activation plan

This is a separate, bounded IAM and source-promotion change. It does not alter
the ECS service, ALB, WAF, DNS, CloudFormation stacks, Cognito client, or
stored secret value.

| Item | Planned value |
| --- | --- |
| Account / profile / region | `337159794548` / `kanbien-dev` / `eu-west-1` |
| Environment | `kanbien/staging` |
| New role | `github-platform-shell-staging-synthetic` |
| Trust | GitHub OIDC for `gordonrose/entity-builder-harness`, `refs/heads/main`, and the exact main-branch subject; no GitHub deployment environment. |
| Inline policy | `ReadOnlyControlledSmokeSecret`, with only `secretsmanager:GetSecretValue` on the declared smoke-client secret ARN. |
| Role tags | `service=platform-shell`, `environment=staging`, `managed-by=github-actions`, and `purpose=protected-synthetic`. |
| Source promotion | Commit the reviewed chat work, merge it into local `main`, and push `main` to `origin` only after the role is verified. |
| First live action | Manually dispatch the source-controlled workflow from `main`; it obtains a temporary token, makes one protected `GET`, and retains only redacted status/latency output. |

### Read-only evidence on 2026-09-22

- `kanbien-dev` authenticated as an administrator SSO session in account
  `337159794548`.
- `github-platform-shell-staging-synthetic` returned `NoSuchEntity`: no role
  currently exists, so there is no hidden pre-existing permission to broaden.
- The existing image-publication role confirms the GitHub OIDC provider and
  main-branch repository conditions exist. The new role deliberately uses the
  branch subject rather than the manually approved `staging` environment
  subject, because an unattended synthetic cannot wait for a deployment
  approval every four hours.

### IAM execution evidence on 2026-09-22

- Created `github-platform-shell-staging-synthetic` at `09:31:57Z`, with only
  the four declared ownership tags.
- Read back its trust policy: the exact GitHub OIDC provider, repository,
  audience, `refs/heads/main`, and main-branch subject all match the reviewed
  source.
- Attached and read back only `ReadOnlyControlledSmokeSecret`. It permits only
  `secretsmanager:GetSecretValue` for the one declared Cognito smoke-client
  secret ARN. No secret value was retrieved or recorded.
- The role was initially dormant until source promotion. The workflow is now on
  remote `main`; its manually dispatched first run completed successfully as
  run `35711517748` from source `9ccad368a34684afaa9b7ed64d7dba85f4b3fae8`,
  returning only the approved `200` status and `266` ms duration. A
  clock-triggered run remains to be observed.

### Exact execution sequence after approval

1. Create the one role with the reviewed
   `github-platform-shell-staging-synthetic-trust.json` and bounded ownership
   tags; create no access keys, users, policy versions, or other identities.
2. Attach only inline policy `ReadOnlyControlledSmokeSecret` from
   `github-platform-shell-staging-synthetic-policy.json`.
3. Read back the role trust policy and inline policy; compare both to the
   repository sources without recording secret values.
4. Commit the source, promote it to local `main`, and push `main` to `origin`.
   The role is intentionally created first: before the workflow exists on
   remote `main`, it is dormant, avoiding a scheduled run that could fail due
   to a missing role.
5. Manually dispatch the workflow from `main`, inspect its redacted result,
   and record only its URL/run identifier, HTTP status, elapsed time, and
   timestamp. Do not record a secret, token, header, or response body.

Rollback is to disable or remove the inline policy and then delete the unused
role only through a separately approved destructive IAM action. Do not delete
the Cognito secret or alter the platform-shell workload as part of this change.

## Proposed target design

These reviewed choices now describe the deployed first target. The remaining
verification work above determines when its readiness record can become ready.

| Concern | Proposed decision | Why |
| --- | --- | --- |
| Infrastructure definition | Focused CloudFormation source units rendered into one AWS CloudFormation template under `infra/04.deploy/03.product/targets/kanbien/staging/` | The repository keeps ingress, edge protection, IAM, rate limiting, logging, and alerting scanable without changing the single reviewed foundation-stack resource graph. |
| Compute | One 512 CPU / 1024 MiB Fargate server task, desired count 1; 128 CPU / 256 MiB is reserved for the collector and worker remains at 0 | The added sidecar has explicit capacity while the first target remains intentionally small. |
| Network | Dedicated service security group: ingress only from the existing ALB security group on TCP 3000; outbound HTTPS only as far as the selected Fargate networking model requires | No direct public inbound path to the task. |
| Routing | New IP target group with `/livez`, dedicated HTTPS listener rule, and Route 53 alias for `staging.platform.kanbien.com` | A host-specific route isolates the proof from legacy root-domain traffic. |
| Public TLS | A foundation-owned ACM public certificate for `platform.kanbien.com` and `*.platform.kanbien.com`, DNS-validated in the existing hosted zone and added as an extra SNI certificate to the existing HTTPS listener | The selected hostname stays stable, future `*.platform.kanbien.com` environments can be covered, and no legacy certificate or listener default is replaced. |
| Authentication | Existing M2M Cognito access-token/JWKS configuration; no client secret delivered to the running service | The service verifies tokens using public keys. The confidential client secret is only for controlled smoke-token acquisition. |
| Shared rate limit | Provider adapter backed by a new DynamoDB fixed-window counter table with TTL and task-role-only `UpdateItem` access | Enforces a shared quota across task replicas without storing raw tokens or a durable personal-data profile. |
| Client address | A target-selected resolver that uses the final ALB-appended `X-Forwarded-For` address only because the task security group admits traffic solely from the ALB | The generic server continues to distrust forwarded headers by default; trust exists only at this reviewed target boundary. |
| Edge protection | New WAFv2 web ACL associated with the existing ALB; every rule is scoped to the new staging host | Gives managed-rule and IP-rate protection before the service while avoiding changes to legacy host behaviour. |
| Observability | ECS `awslogs`, five `OK` infrastructure alarms, and a task-local ADOT collector that sends the reviewed OpenTelemetry metric series to CloudWatch; metrics are queried through PromQL | Separates ordinary logs, infrastructure health, and capability metrics. Delivery is proven; SLO confidence, exporter-loss coverage, dashboard, and capability-alert evidence remain separate work. |
| Runtime image | Build from a digest-pinned Node 22 image; run only the compiled output and production dependencies in a separately digest-pinned Distroless Node 22 non-root image | The deployable artifact omits a shell, package manager, and build toolchain while preserving a reproducible build boundary. |
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
   roles, DynamoDB table, log group, target group, listener rule, DNS-validated
   platform-hostname certificate, WAF, alarms, and SNS topic. Existing ECR,
   Cognito, ALB, default listener certificate, cluster, and hosted zone are
   inputs, not stack resources to replace.
5. Completed on 2026-09-06: applied and inspected the reviewed IAM
   inline-policy update. GitHub can now pass only the platform-shell service
   CloudFormation execution role and update only the platform-shell service
   stack.
6. Completed on 2026-09-06: commit, review, merge, and push the local platform
   slice to `origin/main`. Do not promote a local image.
7. Completed on 2026-09-06: render, review, and execute the foundation CREATE
   change set `foundation-initial-20260906-1915`. The stack reached
   `CREATE_COMPLETE` with its expected 16 additions.
8. Completed on 2026-09-06: repaired the TLS mismatch by adding a
   foundation-owned `platform.kanbien.com` / `*.platform.kanbien.com` ACM
   certificate and attaching it as an additional SNI certificate to the shared
   HTTPS listener. The pushed-source change set had exactly two additions and
   no replacement or modification; it reached `UPDATE_COMPLETE`. ACM reports
   the certificate `ISSUED`, and external TLS verification now passes for
   `staging.platform.kanbien.com`. An application `503` remains expected until
   the service is deployed.
9. Completed on 2026-09-07: run the selected workflow from `origin/main`.
   The workflow built and deployed a digest-pinned Distroless runtime image,
   required a complete zero-critical/zero-high ECR scan, generated and
   attested the SBOM and provenance, created or updated the service stack, and
   passed public liveness plus unauthenticated-route smoke.
10. Completed on 2026-09-22: enabled enhanced Container Insights and verified
    the resulting running-task metric before creating the ECS running-count
    alarm.
11. Completed on 2026-09-22: applied the narrow foundation role changes and
    reduced the live GitHub OIDC role to ECR image publication only.
12. Completed on 2026-09-22: reviewed and applied the service change set. It
    created the three service-owned ECS alarms and deployed task revision 2;
    all five platform alarms were subsequently `OK`.
13. Remaining: prove wrong-permission `403`, `429` from the shared limiter,
    WAF/routing evidence, end-to-end alarm delivery, and a rollback exercise.
14. After tagged foundation resources exist, activate the `service` cost
   allocation tag in the account Billing console, wait for billing visibility,
   configure the target-scoped monthly/forecast budget alerts, and record the
   proof. Do not treat a resource tag as a functioning budget by itself.
15. Completed on 2026-09-22: commit and merge the reviewed observability source
    to `origin/main`, then run the protected GitHub workflow to produce a
    scan-accepted immutable image digest containing that exact target
    composition. That workflow publishes evidence and the digest to ECR; it
    does **not** change CloudFormation, ECS, or the running service. Only then
    create and review a separate observability-delivery change set under the
    governed manual AWS procedure. It adds a task-local ADOT collector,
    non-secret SSM pipeline configuration, a distinct collector log group,
    execution-role read access for that one parameter, and task-role
    `cloudwatch:PutMetricData`. The task grows from 256 CPU / 512 MiB to 512
    CPU / 1024 MiB to reserve sidecar capacity. The rendered template and IAM
    delta showed the expected narrow changes; a protected smoke request
    produced a queryable counter and histogram. Exporter-loss coverage must
    still be proven before an SLO is considered healthy.
16. Remaining hardening: provide a governed controlled-token smoke command
    that declares whether its Secrets Manager value is an opaque raw string or
    structured document, never echoes an input on parser failure, and records
    only safe HTTP outcomes. This is operational tooling, not an ECS runtime
    dependency.

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

The selected TLS repair does not change the shared listener's default
certificate. It adds an SNI certificate only, so the ALB selects it solely
when the client requests a matching `*.platform.kanbien.com` hostname. The
reviewed update has exactly two additions: the foundation-owned certificate and
that attachment.

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
- **TLS repair:** the certificate and SNI attachment were created without
  replacing the existing default certificate. A future retirement requires a
  separately approved stack update that removes only the platform-hostname
  certificate attachment and certificate.

## Execution approval checklist

The initial execution completed on 2026-09-07. A future infrastructure or
service deployment remains blocked until all are true:

- local code, IaC, policy, and target-profile checks pass;
- the exact CloudFormation change set is reviewed;
- the current source is committed and present on `origin/main`;
- immutable image digest, base-image digest, scan, SBOM, and provenance are
  available;
- task and execution IAM roles, WAF scope-down rules, listener priority, and
  SNS subscription are reviewed;
- for any change that includes the running-count alarm, the existing cluster
  is confirmed to use `containerInsights=enhanced` and to publish the reviewed
  `ECS/ContainerInsights` `RunningTaskCount` metric for this service;
- the user explicitly approves the exact staging stack operation in the
  current chat.
