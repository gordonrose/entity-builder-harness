<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.02-rag-rulebook.ecs-fargate.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the ECS Fargate implementation boundary for the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: infra.04-deploy.02-rag-rulebook.readme
  path: infra/04.deploy/02.rag-rulebook/README.md
- id: deploy.rules.02-rag-rulebook.ecs-fargate-deployment
  path: docs/04.deploy/rules/02.rag-rulebook/ecs-fargate-deployment.yml
-->
# ECS Fargate

This directory will own ECS Fargate implementation artifacts for the
RAG/rulebook service.

Future files in this directory should define or reference:

- ECS cluster, service, task definition, and deployment controller
- ECR repository and immutable image digest input
- task execution role and task role
- VPC, subnets, security groups, target group, listener, TLS certificate, and
  DNS boundary
- CloudWatch logs, metrics, alarms, and service health checks
- rollback target and rollback authority
- cost, capacity, quota, and rate-limit controls

Do not add a deployable AWS target here unless the deploy-readiness checker can
validate its manifest and block unsafe execution.

