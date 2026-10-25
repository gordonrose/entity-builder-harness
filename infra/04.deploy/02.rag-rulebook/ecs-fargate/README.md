<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.02-rag-rulebook.ecs-fargate.readme
version: 1
status: active
created_on: "2026-06-30"
updated_on: "2026-10-25"
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

The hosted staging RAG target is retired. Local harness retrieval remains
supported and explicitly selects `RAG_RULEBOOK_PROVIDER=local`.

`cloudformation/` preserves the zero-task service configuration, safe foundation
teardown policies, and ownership of the shared GitHub OIDC provider. The staging
readiness manifest marks this target retired; the old deployment workflow is
inert. Do not recreate it as a fallback for local retrieval.

Use the [CloudFormation retirement notes](cloudformation/README.md) and
[governed retirement procedure](../../../../.agentic/aws/workflows/deploy-rag-rulebook-service.md#hosted-staging-retirement).
Historical deployment instructions and resource evidence remain in Git history
and commit logs.
