<!-- agentic-artifact:
schema: agentic-artifact/v2
id: aws.inventory.kanbien-staging-platform-shell-target-inspection
version: 3
status: draft
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- sre
- architecture
kind: inventory
purpose: Record read-only Kanbien staging AWS inspection evidence for platform shell target planning.
portability:
  class: internal
  targets: []
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.deploy-readiness
  path: infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
-->
# Kanbien Staging Platform Shell Target Inspection

## Scope

Read-only inspection for the platform shell staging target.

- Workflow: `.agentic/aws/workflows/inspect-aws-state.md`
- Profile: `kanbien-dev`
- Region: `eu-west-1`
- Inspected at UTC: `2026-09-05T22:48:00Z`
- Mutation: none

## Inspected State

The existing Kanbien staging AWS boundary is real and active. The caller was
the approved `kanbien-dev` SSO role in account `337159794548`.

- ECS cluster: `kanbien-staging`
- Existing ECS services: `rag-rulebook-staging`, `service-platform`
- Existing ALB listeners: HTTP on port 80 redirects; HTTPS on port 443 has
  host rules for `kanbien.com` and `rag.kanbien.com`, plus the existing default
  forward action.

The existing `service-platform` service remains unrelated to the product
platform shell. It is not a substitute for a new shell service because its
runtime, image, health endpoint, and mounted product composition differ.

### Existing public-site boundary

The customer-facing `kanbien.com` and `www.kanbien.com` names are not an S3 or
CloudFront static-site deployment. Both authoritative Route 53 A-alias records
point to the shared internet-facing ALB. HTTP redirects to HTTPS and the ALB
then redirects `kanbien.com` to `www.kanbien.com`; its default HTTPS action
forwards the request to the `kanbien-staging-app-tg` target group.

That target group had no registered targets at inspection time. The existing
`service-platform` ECS service requested one task but had zero running tasks.
Its container starts by running database migrations and exits with code `1`
when its PostgreSQL connection times out. The configured RDS instance reports
status `inaccessible-encryption-credentials`, so the database is unavailable
to the old service. The resulting ALB response is therefore a `503` because
there is no healthy application target; it is not a DNS failure and is not
caused by the unbuilt platform-shell workload.

The `rag.kanbien.com` HTTPS rule is a separate route to the
`rag-rulebook-staging` target group. The old site's associated Valkey cache is
available, but that does not restore its unavailable database.

**Retention decision:** keep the authoritative `kanbien.com` hosted zone and
the `kanbien.com`, `www.kanbien.com`, and `rag.kanbien.com` records. Do not
delete or repurpose the shared ALB, legacy ECS service, target groups, RDS
instance, Valkey cache, certificate, or their access configuration as part of
the platform-shell proof. Recovery or replacement of the old public site must
have its own governed change plan, dependency/back-up assessment, rollback,
and explicit approval.

### Product platform-shell resources

- ECR repository `platform-shell` exists. It has immutable tags and
  scan-on-push enabled, but contains **zero images**.
- The selected machine-to-machine Cognito user pool, client, and
  `platform-shell/smoke.read` scope exist. The client uses only the
  `client_credentials` grant; this is not a human identity implementation.
- No `kanbien-staging-platform-shell` ECS service exists.
- No platform-shell task-definition family exists.
- No platform-shell ALB target group exists.
- No `staging.platform.kanbien.com` Route 53 record exists, and no matching
  HTTPS ALB host rule exists.
- No `/ecs/kanbien-staging-platform-shell` log group exists.
- No `kanbien-staging-platform-shell` CloudWatch alarms exist.

The result is a real shared staging boundary with selected supporting
resources, but no running or routable platform-shell workload.

## Decisions Already Recorded

- Selected ECR repository name: `platform-shell`
- ECR policy: immutable tags with scan-on-push enabled
- Selected build source policy: only images built from pushed `origin/main`
  count as deployable staging images; local builds are smoke-only.
- Selected tag format:
  `staging-<YYYYMMDD>-<short-sha>-run<github-run-id>`
- Selected deploy reference policy: deploy ECS by immutable image digest, not
  by tag alone.
- Selected evidence policy: require source commit, GitHub workflow run id,
  image digest, base image digest, vulnerability scan, local smoke, and
  deployed smoke for first staging; keep SBOM and attestation as blockers
  before public exposure.
- Selected vulnerability policy: block critical vulnerabilities and fix or
  record explicit risk acceptance for high vulnerabilities before deployment.
- Selected base image policy: pin the base image by digest for official builds.

## Planning Conclusion

The product platform shell can reuse the existing Kanbien staging AWS boundary
as a candidate account, region, cluster, ALB, and certificate boundary. The
readiness blocker is no longer uncertainty about whether an ECR repository or
machine client exists. It is the unexecuted runtime-target slice.

The next AWS change plan must select and create a minimal server-first ECS
target: a task definition, service, security group, target group, HTTPS host
rule, Route 53 record, log group, alarms, and deployment configuration by
immutable image digest. It must also state source/deploy evidence, safe
machine-client secret injection, ingress/rate-limit controls, rollback, and
post-deployment smoke checks. Worker resources, human identity, tenant data,
and business application resources remain out of scope.

The separate public-site recovery decision comes first for the existing
`www.kanbien.com` experience: either repair the legacy service and database
under a dedicated recovery plan, or replace the brochure site through a
separately designed and tested cutover. Neither path authorises unplanned
deletion of the old resources.
