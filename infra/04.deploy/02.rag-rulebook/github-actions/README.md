<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.02-rag-rulebook.github-actions.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the GitHub Actions deployment template boundary for the RAG/rulebook service.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: infra.04-deploy.02-rag-rulebook.readme
  path: infra/04.deploy/02.rag-rulebook/README.md
- id: aws.workflows.deploy-rag-rulebook-service
  path: .agentic/aws/workflows/deploy-rag-rulebook-service.md
-->
# GitHub Actions

This directory will own reviewed deployment workflow templates and deployment
workflow notes for the RAG/rulebook ECS Fargate target.

Live GitHub workflows belong in `.github/workflows/`. Templates or source
workflow definitions may live here when they are used to keep the live workflow
aligned with the infra and deploy-readiness model.

Required future proof:

- protected GitHub environment
- OIDC permission and AWS role assumption
- no long-lived AWS keys
- immutable image and corpus package identity
- deploy-readiness gate before AWS mutation
- ECS service stability and post-deploy context-query smoke test
- rollback and disablement evidence

