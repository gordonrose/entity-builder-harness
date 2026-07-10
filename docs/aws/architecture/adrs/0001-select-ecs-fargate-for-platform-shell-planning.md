<!-- agentic-artifact:
  schema: agentic-artifact/v2
  id: aws.architecture.adr.0001-select-ecs-fargate-for-platform-shell-planning
  version: 1
  status: active
  layer: 04.deploy
  domain: infra.ci-cd
  disciplines:
  - architecture
  - sre
  kind: adr
  purpose: Select ECS Fargate as the first AWS planning runtime family for the platform shell.
  portability:
    class: source-only
    targets: []
  used_by:
  - id: infra.04-deploy.03-product.aws-runtime-family-decision
    path: infra/04.deploy/03.product/aws-runtime-family.decision.yml
  - id: harness.architecture.plan.platform-runtime-implementation
    path: docs/harness/architecture/plans/platform-runtime-implementation-plan.md
-->
# ADR 0001: Select ECS Fargate For Platform Shell Planning

## Status

Accepted.

## Context

The platform runtime shell now has a container image boundary, a server
entrypoint, health endpoints, provider-neutral runtime contracts, worker
mechanics, config validation, security hooks, observability hooks, and a local
image smoke test.

Milestone 9 needs one AWS runtime family so deployment readiness can be proved
against a concrete target instead of a generic cloud idea. The runtime family
selection is still planning-only; it does not authorize AWS mutation, DNS
changes, IAM changes, image publishing, or production exposure.

Repo-side inspection shows an existing deploy track already uses ECS Fargate
for the RAG/rulebook staging service. That does not make the product platform
shell target ready, but it does mean this repo already has ECS Fargate
deployment vocabulary, readiness manifest shape, and workflow examples.

The platform shell has both HTTP server and background worker concerns. It
needs a target model that can support long-running containers, separate
server/worker services, ALB or equivalent ingress, health checks, logs,
scaling, deployment circuit breakers, rollback, and queue integration.

## Decision

Select `ecs-fargate` as the first AWS runtime family for platform shell
deployment planning.

This selection is a deployment planning target, not an app contract. Apps keep
declaring provider-neutral routes, jobs, health checks, config schemas,
permissions, lifecycle hooks, and deployment requirements through platform
contracts and public app manifests.

Future runtime families such as AWS Lambda, App Runner, EKS, or non-AWS
targets may be added through governed provider adapters and deployment
profiles. The adapter layout is:

```text
platform/adapters/<provider>/<adapter-type>/<service-name>/
```

For ECS Fargate planning, deployment readiness must name task definitions,
server and worker service topology, network boundaries, ingress, TLS, target
groups, health checks, scaling, rollback, alarms, logs, secrets, cost limits,
and exact mutation plans before any AWS execution.

## Consequences

Milestone 10 can target one runtime family and define target-specific readiness
checks.

ECS Fargate-specific assumptions stay in deploy/AWS planning artifacts,
provider adapters, and infra implementation. They do not move into ordinary
app code or provider-neutral platform runtime contracts.

The current blocker for AWS execution is not runtime-family ambiguity. The
remaining blockers are target account/profile, region, environment, cluster
and service target, image digest, secret store, queue/storage requirements,
TLS/DNS decisions, alarms, rollback authority, and explicit mutation approval.
