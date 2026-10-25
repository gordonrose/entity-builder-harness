<!-- agentic-artifact:
schema: agentic-artifact/v3
id: deploy.plan.migration.operational-realization-authority
version: 1
status: active
created_on: "2026-10-24"
updated_on: "2026-10-25"
layer: 04.deploy
domain: migration
disciplines: [agentic, architecture, sre]
kind: migration-plan
purpose: Consolidate deployment proof authority under its deployment owner while retaining legacy compatibility pointers.
portability: { class: reusable, targets: [entity-builder] }
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
-->
# Operational Realization Authority Migration

## Scope and compatibility

Move the authoritative standard and workflow from
`.agentic/01.harness/standards/operational-realization-gate.md` and
`.agentic/01.harness/workflows/operational-realization-gate.md` to the matching
`standards/` and `workflows/` paths under `.agentic/04.deploy/`. Retain the old
paths as human-readable compatibility pointers, including the prior bounded
PostgreSQL anchor. Existing contract schemas, template paths, schema IDs,
compiler commands and script homes remain compatible. The provider procedure
moves into `.agentic/aws/standards/operational-realization-applicability.md`.

This implements existing owner routing; it does not move the AWS provider
namespace or grant execution, publication, secret access, commits or live
infrastructure authority. The user authorized local implementation only, so
this plan is prepared with the change for review without making a commit.

## Reference inventory

Before changing active references, both commands below were run on 2026-10-24:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh .agentic/01.harness/standards/operational-realization-gate.md .agentic/04.deploy/standards/operational-realization-gate.md
bash scripts/01.harness/plan-artifact-path-migration.sh .agentic/01.harness/workflows/operational-realization-gate.md .agentic/04.deploy/workflows/operational-realization-gate.md
```

Each reported 21 exact references. Standard buckets were workflow/generated
recognition, session history, and other (deploy docs and package command).
Workflow buckets additionally included script metadata and generated routing.
The destination files did not exist. Supplementary relative-link search found
AWS, product and template guide references to the bounded applicability clause.

Update active workflows, script/template metadata, package checks, docs and
indexes. Regenerate recognition sources using their owner command. Preserve
historical `commitLogs/` unchanged. Compatibility pointers deliberately retain
old artifact identities; canonical authority receives deployment identities.

## Validation and recovery

Run both migration checkers with `--allow-active-old-path` for retained
pointers, the realization compiler smoke suite, metadata header validation,
recognition generation/validation, deployment placement validation for new
canonical paths, and `git diff --check`. No scripts or schemas move, so no
runtime or provider migration is required. Check completion remains in the
current session record rather than being inferred from this plan.

If local validation fails, repair active references or pointer links within
this change before use. Preserve both old pointers and canonical authority;
do not delete audit history or roll back unrelated edits. Execution approval
requirements remain with the provider owner throughout.

## ADR disposition

`docs/04.deploy/adrs/0042-separate-change-and-deployment-proof-ownership.md`
records the durable authority/compatibility decision. No layer namespace,
public bootstrap API, live provider behavior or schema version is changed.
