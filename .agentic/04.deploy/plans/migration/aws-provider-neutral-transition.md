<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.aws-provider-neutral-transition
version: 1
status: draft
created_on: "2026-10-06"
updated_on: "2026-10-20"
layer: 04.deploy
domain: migration
disciplines:
- agentic
- architecture
- sre
kind: migration-plan
purpose: Safely establish provider-neutral deployment governance before any later migration of active AWS-specific artifacts.
portability:
  class: source-only
  targets: []
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
- id: deploy.layer.readme
  path: .agentic/04.deploy/README.md
-->
# AWS to Provider-Neutral Deployment Governance Transition

## Decision

Establish `.agentic/04.deploy/` as the provider-neutral deployment governance
home. Do not move `.agentic/aws/` in this bootstrap phase. The legacy AWS path
remains authoritative for all AWS inspection, planning, execution, and
PostgreSQL Stage 6 controls.

## Bootstrap Scope

This phase creates only the new generic layer, its migration-plan home, its
future provider-adapter home, the Target Alignment Preflight workflow and
standard, the Declaration Coverage workflow, standard, schema, and bounded
platform-shell contract, the lifecycle map and stage-ownership standard, and the
non-executable capability home under `scripts/04.deploy/lifecycle/`. It changes
no AWS resource, provider workflow, PostgreSQL source, target definition, or
execution authority.

## Protected PostgreSQL Work

Do not move, rewrite, or semantically alter these surfaces during bootstrap:

- `.agentic/aws/plans/implementation/postgresql-stage6-restart-2026-10-03.md`
- `.agentic/03.product/plans/implementation/postgresql-relational-persistence-reference-v1.md`
- `docs/aws/kanbien-staging-postgresql-relational-reference-v1-*`
- `scripts/04.deploy/run-platform-shell-postgresql-relational-smoke/`
- `infra/04.deploy/03.product/targets/kanbien/staging/`

No PostgreSQL Stage 6 live operation may be run as part of this transition.

## Later Migration Prerequisites

Before proposing a move from `.agentic/aws/` to
`.agentic/04.deploy/providers/aws/`:

1. Run the governed path-migration planner and record its full reference
   inventory.
2. Choose and test an old-path compatibility mechanism.
3. Record the baseline commit and protected PostgreSQL content hashes.
4. Update active routers, workflows, scripts, generated artifacts, and tests
   in reviewable batches; preserve historical session logs unchanged.
5. Run the migration checker, affected harness checks, deployment checks, and
   PostgreSQL local controller checks without invoking live execution modes.
6. Obtain separate approval for the actual provider-path migration.

## Initial Target Alignment Direction

Target Alignment Preflight will first define a provider-neutral comparison
contract and offline validation. An AWS-specific read adapter remains future
work and must retain the existing `.agentic/aws/` safety and approval boundary
until migrated under an approved plan.
