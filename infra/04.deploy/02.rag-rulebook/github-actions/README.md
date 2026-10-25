<!-- agentic-artifact:
schema: agentic-artifact/v3
id: infra.04-deploy.02-rag-rulebook.github-actions.readme
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

`.github/workflows/deploy-rag-rulebook-staging.yml` is an inert retirement
tombstone: its only job is always skipped, it grants no token permissions and
contains no deployment commands or AWS credential setup. Disable the workflow
in GitHub as part of the governed retirement. Preserve its run history and the
shared GitHub environment.

The retired staging manifest cannot pass deployment readiness. Harness context
retrieval uses `RAG_RULEBOOK_PROVIDER=local`. Recommissioning needs a separately
reviewed and explicitly approved change; old workflow revisions are historical
evidence, not an authorised deployment route.

See [hosted staging retirement](../../../../.agentic/aws/workflows/deploy-rag-rulebook-service.md#hosted-staging-retirement).
