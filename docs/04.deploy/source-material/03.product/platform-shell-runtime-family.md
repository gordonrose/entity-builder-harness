<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.03-product.platform-shell-runtime-family
version: 3
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: source-material
purpose: Record the platform shell runtime-family and target-profile planning decisions for deploy/RAG retrieval.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.rules.03-product.platform-shell-runtime-family
  path: docs/04.deploy/rules/03.product/platform-shell-runtime-family.yml
- id: harness.architecture.adr.0028-use-client-environment-deployment-target-profiles
  path: docs/harness/architecture/adrs/0028-use-client-environment-deployment-target-profiles.md
-->
# Platform Shell Runtime Family

## Purpose

This source material records the deployment planning decision for the first AWS
runtime family of the product platform shell.

It exists so future deploy planning, RAG retrieval, and human explanations can
answer which runtime family was selected, how client/environment deployment
targets are represented, and what those decisions do and do not authorize.

## Decision

Select `ecs-fargate` as the first AWS runtime family for platform shell
deployment planning.

This is a planning decision only. It does not authorize AWS mutation, DNS
changes, IAM changes, image publishing, or production exposure.

ECS Fargate is the first planning target because the platform shell has both
HTTP server and background worker concerns. ECS Fargate can model separate
server and worker services, long-running containers, ALB health checks,
service stability, logs, scaling, deployment circuit breakers, rollback, and
queue integration.

## Boundary

ECS Fargate is not part of the app contract.

Apps should keep declaring provider-neutral routes, jobs, health checks,
config schemas, permissions, lifecycle hooks, and deployment requirements
through public platform contracts and app manifests.

Platform and deploy composition decide which runtime adapters and deployment
profiles satisfy those needs.

Future runtime families such as AWS Lambda, App Runner, EKS, or non-AWS
targets may be added through governed provider adapters and deployment
profiles.

Platform adapters use the path shape:

```text
platform/adapters/<provider>/<adapter-type>/<service-name>/
```

Examples include:

- `platform/adapters/aws/runtime/ecs-fargate/`
- `platform/adapters/aws/runtime/lambda/`
- `platform/adapters/aws/runtime/app-runner/`
- `platform/adapters/aws/queue/sqs/`

## Deployment Target Profiles

Deployment target selection is profile-driven. Client, source repository,
cloud provider, account or subscription, region, runtime family, adapter, and
readiness proof live in deploy target profiles, not ordinary app feature code
or provider-neutral platform runtime internals.

Product platform shell targets use this path shape:

```text
infra/04.deploy/03.product/targets/<client>/<environment>/
```

The first scaffolded profile is:

```text
infra/04.deploy/03.product/targets/kanbien/staging/deploy-readiness.yml
```

A target profile should name:

- `client.id`, such as `kanbien`;
- `environment.id`, such as `staging` or `production`;
- source provider, repository, ref, commit, workflow path, and workflow run id;
- cloud provider and account, subscription, tenant, role/profile, or region;
- runtime provider, runtime family, and selected adapter path;
- auth provider, token validation mode, issuer/JWKS/app-client config,
  target authz mapping source, route exposure policy, health exposure policy,
  CORS allowlist, rate-limit keying, and secret/config source;
- target-specific blockers, readiness proof, smoke proof, and rollback proof.

Adding a future client, repository, AWS account, Azure subscription, or runtime
family should require a new target profile and, where necessary, a governed
provider adapter. It should not require changing ordinary app feature code.

## Auth Provider Target Profile

The first product platform shell auth provider path is Amazon Cognito, recorded
in `docs/aws/architecture/adrs/0002-select-cognito-for-platform-shell-auth.md`.

Cognito is a target auth provider choice, not an app contract. Apps still
declare app-owned permissions through app mounts. Target authz mappings may
grant only permissions declared by apps included in the product target.

For Kanbien staging, the target profile must record:

- `auth.provider: cognito`;
- Cognito user-pool issuer, JWKS URI, app client id, and `token_use: access`;
- local token-validation proof through `platform/security`;
- the source of group, scope, or claim to permission mappings;
- validation that mapped permissions are declared by mounted apps;
- protected dummy-route proof for `401`, `403`, and success paths;
- public/private route classification and `/livez`/`/readyz` exposure policy;
- CORS allowlist source and concrete origins before public exposure;
- rate-limit keying based on principal, token/session identity, trusted
  forwarded IP, or an approved fallback;
- secret/config source without committing secret values.

Readiness remains blocked until those values and deployment smoke proofs are
present for the target.

## Blockers Before AWS Mutation

Before any AWS execution for a specific target profile, the product platform
shell must record:

- client and environment identity;
- source provider, repository, ref, commit SHA, workflow path, and workflow run
  identity;
- cloud provider, AWS account/profile or OIDC role, and region;
- ECS cluster and service target;
- server and worker task topology;
- VPC, subnet, security group, ALB, target group, TLS, and DNS choices or
  explicit deferrals;
- immutable image digest and base image digest;
- ECR repository and publish workflow or governed equivalent;
- secret store, queue resources, storage resources, and environment values or
  explicit deferrals;
- auth provider, Cognito issuer/JWKS/app-client values, target authz mapping
  source, CORS allowlist, rate-limit keying, health exposure policy, and
  secret/config source;
- deployment circuit breaker, rollback target, rollback authority, alarms,
  cost limit, owner, and escalation path;
- source commit, workflow run identity, SBOM or accepted risk record,
  vulnerability scan or accepted risk record, and deployment smoke proof.

## Non-Goals

Do not deploy from this decision.

Do not treat the existing RAG/rulebook ECS Fargate staging target as the
product platform shell target.

Do not put ECS Fargate-specific assumptions into ordinary app feature code or
provider-neutral platform runtime contracts.

Do not create one global deployment target when client, environment, provider,
account, subscription, region, and runtime family can vary by client.
