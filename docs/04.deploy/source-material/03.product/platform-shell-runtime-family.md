<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.source-material.03-product.platform-shell-runtime-family
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: source-material
purpose: Record the platform shell AWS runtime-family planning decision for deploy/RAG retrieval.
portability:
  class: internal
  targets: []
used_by:
- id: deploy.rules.03-product.platform-shell-runtime-family
  path: docs/04.deploy/rules/03.product/platform-shell-runtime-family.yml
-->
# Platform Shell Runtime Family

## Purpose

This source material records the deployment planning decision for the first AWS
runtime family of the product platform shell.

It exists so future deploy planning, RAG retrieval, and human explanations can
answer which runtime family was selected and what that decision does and does
not authorize.

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

## Blockers Before AWS Mutation

Before any AWS execution, the product platform shell must record:

- AWS account/profile or OIDC role;
- region and environment;
- ECS cluster and service target;
- server and worker task topology;
- VPC, subnet, security group, ALB, target group, TLS, and DNS choices or
  explicit deferrals;
- immutable image digest and base image digest;
- ECR repository and publish workflow or governed equivalent;
- secret store, queue resources, storage resources, and environment values or
  explicit deferrals;
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
