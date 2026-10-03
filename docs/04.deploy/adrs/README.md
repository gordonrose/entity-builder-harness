<!-- agentic-artifact:
schema: agentic-artifact/v2
id: deploy.adrs.readme
version: 1
status: active
layer: 04.deploy
domain: infra.ci-cd
disciplines:
- agentic
- sre
kind: adr-readme
purpose: Define the owner-aligned ADR home for deployment and operations decisions.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.adr.0032-use-owner-aligned-adr-roots
  path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- id: deploy.corpus.readme
  path: docs/04.deploy/README.md
- id: rag-rulebook.migration-plan.prototype-corpus-domain-split
  path: .agentic/02.rag-rulebook/plans/migration/prototype-corpus-domain-split.md
-->
# 04.deploy ADRs

This directory records durable architecture decisions owned by deployment and
operations: cloud governance, deploy target profiles, runtime families,
infrastructure boundaries, release readiness, rollback, and runtime operation
tradeoffs.

Use this root for deploy-owned ADRs that are corpus history. AWS workflow
governance stays under `.agentic/aws/`; deployable definitions and target
profiles stay under `infra/04.deploy/`; deploy source material and structured
rules stay under the matching `docs/04.deploy/` corpus subdirectories.

The old prototype ADR pointers have been retired. Use this owner-aligned ADR
root directly for deploy-owned decision history.
