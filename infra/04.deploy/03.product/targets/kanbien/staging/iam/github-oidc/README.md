<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.iam.github-oidc.readme
version: 3
status: active
layer: 04.deploy
domain: infra.access
disciplines:
- security
- sre
kind: capability-readme
purpose: Index the separately scoped GitHub OIDC IAM policy and trust-policy source for Kanbien staging platform-shell operations.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
- id: deploy.script.verify-platform-shell-synthetic-scheduler
  path: scripts/04.deploy/verify-platform-shell-synthetic-scheduler/script.sh
-->
# Kanbien Staging Platform-Shell GitHub OIDC IAM Source

Each GitHub operational purpose has its own role. The target profile names the
role, source files, deployment state, and any live-policy inspection evidence.
The JSON files in this folder are reviewed source, not proof that a role exists
in AWS.

| Files | Role purpose | Allowed AWS capability | Trust boundary |
| --- | --- | --- | --- |
| `github-platform-shell-staging-deploy-policy.json` and `github-platform-shell-staging-deploy-trust.json` | Build and publish the immutable platform-shell image. | ECR image operations for `platform-shell` only. | GitHub Actions for this repository's `main` branch through the protected `staging` environment. |
| `github-platform-shell-staging-synthetic-policy.json` and `github-platform-shell-staging-synthetic-trust.json` | Run the protected staging synthetic. | Inline policy `ReadOnlyControlledSmokeSecret` reads exactly the declared Cognito machine-client secret. | GitHub Actions for this repository's `main` branch only; no deployment environment or repository-secret fallback. |
| `github-platform-shell-staging-reconciliation-policy.json` and `github-platform-shell-staging-reconciliation-trust.json` | Reconcile declared staging deployment controls. | Exact CloudFormation stack/drift reads, artifact-bucket control reads, one budget read, and caller identity only. | GitHub Actions for this repository's `main` branch only; it cannot deploy, alter stacks, read secrets, or operate ECS/RDS. |

The synthetic role is intentionally not permitted to deploy an image, change a
CloudFormation stack, manage ECS, administer Cognito, or read a wildcard set of
secrets. Its scheduled workflow is best-effort operational evidence, not a
replacement for the future governed platform scheduler.
