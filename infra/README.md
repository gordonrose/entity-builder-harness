<!-- agentic-artifact:
schema: agentic-artifact/v2
id: infra.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- sre
kind: guide
purpose: Define the repository implementation boundary for infrastructure and deployment definitions.
portability:
  class: internal
  targets: []
used_by:
- id: harness.architecture.rules.layers.infra
  path: docs/harness/architecture/rules/layers/infra.yml
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Infra

`infra/` is the implementation home for infrastructure-as-code, deployment
definitions, container packaging boundaries, environment manifests, and
deployment workflow templates.

This directory is not the deploy corpus. Human-readable deployment knowledge
belongs in `docs/04.deploy/`; executable checks belong in `scripts/04.deploy/`;
AWS operating workflows belong in `.agentic/aws/`.

Use `infra/**` for concrete deployable definitions such as:

- Terraform, CDK, Pulumi, CloudFormation, or Kubernetes sources
- container image packaging boundaries and runtime manifests
- ECS task definitions, services, load balancer, DNS, certificate, and IAM
  definitions
- GitHub Actions deployment workflow templates and environment definitions
- non-secret environment manifests consumed by deployment checks

Do not store secrets, private keys, credentials, live tokens, or sensitive
runtime dumps here.

