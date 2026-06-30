<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.02-rag-rulebook.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the infra implementation boundary for deploying the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
- id: aws.workflows.deploy-rag-rulebook-service
  path: .agentic/aws/workflows/deploy-rag-rulebook-service.md
-->
# RAG/Rulebook Deploy Infra

This directory is the concrete infrastructure implementation boundary for the
first hosted RAG/rulebook service.

The first target is ECS Fargate behind an HTTPS boundary, deployed from GitHub
Actions with OIDC and immutable service/corpus artifacts.

This scaffold is intentionally non-mutating. It does not deploy, publish, call
AWS, or configure GitHub. It only creates the correct home for the files needed
to make that deployment safe.

## Layout

- `image/` owns the container packaging boundary for the existing service.
- `ecs-fargate/` owns ECS Fargate target definitions and future IaC.
- `github-actions/` owns reviewed deployment workflow templates and notes.

Live GitHub workflow files still live in `.github/workflows/`. If a workflow is
generated from or mirrored by an infra template, the relationship must be
documented here and validated by a deploy-readiness check.

## Boundaries

- Service source remains in `.agentic/02.rag-rulebook/service/`.
- Local service scripts remain in `scripts/02.rag-rulebook/`.
- Deploy checks remain in `scripts/04.deploy/`.
- Deploy source material and generated rules remain in `docs/04.deploy/`.
- AWS operating workflows remain in `.agentic/aws/`.

## Stop Conditions

Do not deploy from this directory until the deploy-readiness manifest passes
without planning overrides and names real, non-secret evidence for GitHub OIDC,
AWS account and region, ECR repository, ECS cluster/service, ALB/TLS boundary,
image digest, corpus package identity, health checks, rollback, logs, alarms,
cost controls, and owner escalation.

