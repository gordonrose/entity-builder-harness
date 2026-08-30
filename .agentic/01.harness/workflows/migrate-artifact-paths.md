<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.workflows.migrate-artifact-paths
version: 1
status: active
layer: 01.harness
domain: migration
disciplines:
- agentic
kind: workflow
purpose: Govern reusable planning and validation for moving, renaming, retiring, or
  removing repository artifact paths.
portability:
  class: required
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.workflows.change-harness
  path: .agentic/01.harness/workflows/change-harness.md
- id: harness.standards.artifact-path-migrations
  path: .agentic/01.harness/standards/artifact-path-migrations.md
-->

# Migrate Artifact Paths

## Use When

Use this workflow for tasks that move, rename, retire, or remove committed
files or directories.

For harness layer or owner namespace renames, include both the `.agentic/`
namespace and the matching `scripts/` namespace in the migration plan.

Migration plans are durable artifacts. Session logs should reference those plan
artifacts and record chat activity against them; they should not be the only
place where a harness-built plan lives.

## Required Gates

Run the active workflow dirty-worktree gate before editing:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping
```

## Step 1: Read The Standard

Consult:

```txt
.agentic/01.harness/standards/artifact-path-migrations.md
```

## Step 2: Create Or Update The Plan Artifact

Create or update a committed `kind: migration-plan` artifact before changing
active references.

Use this location for `.agentic/` layer-owned migration plans:

```txt
.agentic/<affected-layer>/plans/migration/<slug>.md
```

For implementation plans, use the sibling implementation folder:

```txt
.agentic/<affected-layer>/plans/implementation/<slug>.md
```

For a layer namespace rename, the affected layer is the proposed canonical layer
path. It is acceptable to create the new layer root first only to hold the
migration plan.

## Step 3: Plan References

Run the planner for each old path and proposed new path:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh <old-path> <new-path>
```

Record the planner output, compatibility choice, affected reference buckets,
validation checks, and rollback or recovery approach in the migration plan
artifact.

For a layer namespace rename, run one plan for the process path and one for the
script owner path.

Example:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh .agentic/<old-layer> .agentic/<new-layer>
bash scripts/01.harness/plan-artifact-path-migration.sh scripts/<old-layer> scripts/<new-layer>
```

## Step 4: Choose Compatibility

Choose the old-path disposition:

- `alias`
- `wrapper`
- `pointer`
- `retired`

Stop if active old-path references exist and none of these choices is safe.

## Step 5: Edit Canonical Surfaces

Update active routers, workflows, standards, scripts, tests, bootstrap exports,
and templates to name the canonical path.

Do not rewrite historical session logs only to modernize old paths.

## Step 6: Validate

Run the checker:

```bash
bash scripts/01.harness/check-artifact-path-migration.sh <old-path> <new-path>
```

If the migration plan artifact names the old path as migration evidence, pass it
explicitly so the checker still fails on other active old-path references:

```bash
bash scripts/01.harness/check-artifact-path-migration.sh \
  --plan <migration-plan-path> \
  <old-path> <new-path>
```

Use `--allow-active-old-path` only when an alias, wrapper, or pointer is part of
the approved compatibility plan:

```bash
bash scripts/01.harness/check-artifact-path-migration.sh --allow-active-old-path <old-path> <new-path>
```

Then run any affected workflow, classifier, bootstrap, smoke, and metadata
checks named by the migration plan.

The migration helper smoke test is:

```bash
bash scripts/01.harness/smoke-test-artifact-path-migration.sh
```

## Step 7: Record Outcome

Record in the session log:

- migration-plan artifact path and status;
- old path
- new path
- compatibility choice
- active reference buckets updated
- checks run
- ADR disposition

Create or update an ADR when the migration changes a durable namespace, public
bootstrap surface, compatibility promise, or layer layout.
