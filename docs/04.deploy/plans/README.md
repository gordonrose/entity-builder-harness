<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.plans.readme
version: 4
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

For Kanbien/staging PostgreSQL Stage 6 only, the [bounded applicability clause](../../../.agentic/01.harness/standards/operational-realization-gate.md#bounded-postgresql-stage-6-applicability)
is effective only after explicit adoption and approval of its concrete
execution plan. Until then the current requirements remain effective.
The generic programme prerequisites below remain the default for other work.
No plan index entry grants provider execution authority.

This folder holds deploy-owned programmes that turn an architectural decision
into controlled, staged work. A plan states what can be implemented in source,
what needs a separate AWS approval, the expected cost and permissions, rollback,
and the evidence needed to close each stage.

Plans do not authorise AWS mutations on their own. The governing execution
workflow remains `.agentic/aws/workflows/execute-approved-aws-change.md`.

| Plan | Purpose |
| --- | --- |
| [`kanbien-staging-aws-change-reliability-programme.md`](kanbien-staging-aws-change-reliability-programme.md) | Prevent source/live IAM and CloudFormation drift-detection dependency failures before a staging change reaches AWS. |
| [`kanbien-staging-platform-foundation-convergence-v1.md`](kanbien-staging-platform-foundation-convergence-v1.md) | Orchestrate data governance, PostgreSQL, scheduler/time, storage, and observability foundations through source, reconciliation, change-set, proof, recovery, and closeout gates. |
| [`operational-realization-v2-programme.md`](operational-realization-v2-programme.md) | Define the complete runtime graph and target-adapter proof required before a candidate can reach a live service. |
| [`kanbien-staging-image-execution-preflight-v1.md`](kanbien-staging-image-execution-preflight-v1.md) | Superseded symptom-focused draft retained only as a trace of the first rejected approach. |
| [`operational-realization-gate-programme.md`](operational-realization-gate-programme.md) | Require a complete provider-neutral execution graph and evidence sequence before any live capability operation. |
| [Controlled recovery report](controlled-recovery-report-2026-10-03.md) | Verified evidence, completed local source restoration, preservation boundaries and the exact proposed shared merge. |
| [Replacement deployment proposal](controlled-recovery-replacement-proposal-2026-10-03.md) | Proposed bounded delivery and parallel learning after recovery; no implementation or deployment approval. |
