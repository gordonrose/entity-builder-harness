<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.02-rag-rulebook.readme
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

The hosted staging deployment is retired. Harness context queries use
`RAG_RULEBOOK_PROVIDER=local`; local service code, corpus and retrieval tooling
remain supported. These infrastructure files preserve the resource ownership
and safe teardown configuration; they are not an active deployment path.

- `image/` retains service image packaging for local use.
- `ecs-fargate/cloudformation/` retains zero-task service configuration,
  explicit log/secret retention and shared OIDC ownership.
- `environments/staging/deploy-readiness.yml` marks the target retired.
- The old GitHub workflow is inert and has no AWS permissions.

Follow [hosted staging retirement](../../../.agentic/aws/workflows/deploy-rag-rulebook-service.md#hosted-staging-retirement)
for authorised teardown and evidence. Recommissioning requires a separate
reviewed change and explicit approval. Historical deployment evidence remains
in commit logs and Git history.
