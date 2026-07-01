<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.scripts.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: capability-readme
purpose: Index deploy-layer executable checks and helpers.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: deploy.script.verify-rag-rulebook-deploy-readiness
  path: scripts/04.deploy/verify-rag-rulebook-deploy-readiness/script.sh
- id: deploy.script.validate-container-boundaries
  path: scripts/04.deploy/validate-container-boundaries/script.sh
-->
# Deploy Scripts

Deploy scripts provide executable, deploy-owned checks.

Commands in this folder must fail closed for deploy execution and must not
mutate cloud state unless their README and workflow explicitly declare a
mutating effect and require current-chat approval.

Current commands:

- `validate-container-boundaries/`: read-only Dockerfile and container image
  placement validation so deployable images stay under governed `infra/**`
  image directories.
- `verify-rag-rulebook-deploy-readiness/`: read-only manifest validation for
  RAG/rulebook GitHub-to-AWS deployment readiness.
