<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plans.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- architecture
- security
- sre
kind: plan-readme
purpose: Index deploy-owned implementation programmes before their infrastructure mutations are authorised.
portability:
  class: reusable
  targets:
  - entity-builder
used_by:
- id: deploy.corpus.readme
  path: docs/04.deploy/README.md
-->
# Deployment Implementation Plans

This folder holds deploy-owned programmes that turn an architectural decision
into controlled, staged work. A plan states what can be implemented in source,
what needs a separate AWS approval, the expected cost and permissions, rollback,
and the evidence needed to close each stage.

Plans do not authorise AWS mutations on their own. The governing execution
workflow remains `.agentic/aws/workflows/execute-approved-aws-change.md`.

| Plan | Purpose |
| --- | --- |
| [`kanbien-staging-aws-change-reliability-programme.md`](kanbien-staging-aws-change-reliability-programme.md) | Prevent source/live IAM and CloudFormation drift-detection dependency failures before a staging change reaches AWS. |
