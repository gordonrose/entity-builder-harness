<!-- agentic-artifact:
owner: harness
kind: workflow
purpose: Govern reusable planning and validation for moving, renaming, retiring, or removing repository artifact paths.
domain: migration
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/workflows/change-harness.md
  - .agentic/01.harness/standards/artifact-path-migrations.md
-->

# Migrate Artifact Paths

## Use When

Use this workflow for tasks that move, rename, retire, or remove committed
files or directories.

For harness layer or owner namespace renames, include both the `.agentic/`
namespace and the matching `scripts/` namespace in the migration plan.

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

## Step 2: Plan References

Run the planner for each old path and proposed new path:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh <old-path> <new-path>
```

For a layer namespace rename, run one plan for the process path and one for the
script owner path.

Example:

```bash
bash scripts/01.harness/plan-artifact-path-migration.sh .agentic/01.harness .agentic/01.harness
bash scripts/01.harness/plan-artifact-path-migration.sh scripts/01.harness scripts/01.harness
```

## Step 3: Choose Compatibility

Choose the old-path disposition:

- `alias`
- `wrapper`
- `pointer`
- `retired`

Stop if active old-path references exist and none of these choices is safe.

## Step 4: Edit Canonical Surfaces

Update active routers, workflows, standards, scripts, tests, bootstrap exports,
and templates to name the canonical path.

Do not rewrite historical session logs only to modernize old paths.

## Step 5: Validate

Run the checker:

```bash
bash scripts/01.harness/check-artifact-path-migration.sh <old-path> <new-path>
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

## Step 6: Record Outcome

Record in the session log:

- old path
- new path
- compatibility choice
- active reference buckets updated
- checks run
- ADR disposition

Create or update an ADR when the migration changes a durable namespace, public
bootstrap surface, compatibility promise, or layer layout.
