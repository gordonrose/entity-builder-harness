<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.scripts.readme
version: 4
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
- id: deploy.script.verify-platform-shell-deploy-readiness
  path: scripts/04.deploy/verify-platform-shell-deploy-readiness/script.sh
- id: deploy.script.validate-container-boundaries
  path: scripts/04.deploy/validate-container-boundaries/script.sh
-->
# Deploy Scripts

Deploy scripts provide executable, deploy-owned checks.

Commands in this folder must fail closed for deploy execution and must not
mutate cloud state unless their README and workflow explicitly declare a
mutating effect and require current-chat approval.

Current commands:

- `build-platform-shell-image/`: local-only Docker image build wrapper for the
  provider-neutral platform shell.
- `smoke-test-platform-shell-image/`: local-only image smoke test for platform
  shell `/livez` and `/readyz`.
- `run-platform-shell-controlled-smoke/`: locally validates, or with explicit
  target approval performs, one fixed protected staging request using an
  in-memory Cognito token and redacted status-only output.
- `provision-platform-shell-negative-authz-client/`: locally validates, or
  with explicit current-chat approval creates the one separately scoped Cognito
  machine client and its named secret for the bounded staging `403` proof.
- `run-platform-shell-negative-authz-smoke/`: locally validates, or after
  post-deployment inspection and explicit current-chat approval performs the
  one fixed valid-token, unmapped-scope staging request that must return `403`.
- `verify-platform-shell-synthetic-scheduler/`: read-only policy check for the
  temporary GitHub Actions protected-route synthetic workflow and its separate
  one-secret-read IAM role source.
- `validate-container-boundaries/`: read-only Dockerfile and container image
  placement validation so deployable images stay under governed `infra/**`
  image directories.
- `verify-platform-shell-deploy-readiness/`: read-only manifest validation for
  product platform shell deployment readiness, including explicit blocker
  coverage for planning-only evidence.
- `verify-platform-shell-deployment-workflow/`: read-only supply-chain gate
  that makes the staging workflow scan, create an SPDX SBOM, and attest the
  immutable image before it can deploy the service stack.
- `verify-rag-rulebook-deploy-readiness/`: read-only manifest validation for
  RAG/rulebook GitHub-to-AWS deployment readiness.
