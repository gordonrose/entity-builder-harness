<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.04-deploy.03-product.targets.kanbien.staging.iam.readme
version: 3
status: active
layer: 04.deploy
domain: infra.access
disciplines:
- security
- sre
kind: capability-readme
purpose: Index the target-specific IAM source by operational identity boundary.
portability:
  class: internal
  targets:
  - kanbien/staging
used_by:
- id: infra.04-deploy.03-product.targets.kanbien.staging.target-profile
  path: infra/04.deploy/03.product/targets/kanbien/staging/target-profile.yml
-->
# Kanbien Staging IAM Source

This folder indexes target-specific IAM source that is intentionally managed
outside the platform-shell CloudFormation stack.

| Folder | Owns | Does not own |
| --- | --- | --- |
| [`github-oidc/`](github-oidc/README.md) | GitHub Actions trust policies and least-privilege permission policies for separately managed operational identities. | ECS task and execution roles, which belong to the platform-shell Foundation CloudFormation stack. |

The distinction is deliberate: a running workload's roles change with its
stack, while GitHub's account-level operational identities have a separate
trust boundary and deployment lifecycle.
