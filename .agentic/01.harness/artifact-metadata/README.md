<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.capability.artifact-metadata
version: 2
status: active
created_on: "2026-06-24"
updated_on: "2026-10-20"
layer: 01.harness
domain: metadata
disciplines:
  - agentic
kind: readme
purpose: Index the harness artifact metadata capability, including lifecycle schemas, taxonomy, maintenance, and indexing.
portability:
  class: required
  targets:
    - llm-workbench
    - entity-builder
    - design-system-builder
used_by:
  - id: harness.readme.01-harness
    path: .agentic/01.harness/README.md
  - id: harness.workflow.change-harness
    path: .agentic/01.harness/workflows/change-harness.md
-->

# Artifact Metadata Capability

This capability owns the metadata model used to describe harness artifacts and
to build future machine-readable indexes for agent navigation, migration
planning, and cross-repo extraction.

## Files

- `standard.md` defines the preferred `agentic-artifact/v3` metadata shape, lifecycle dates,
  versioning policy, stable artifact IDs, and ID-first references.
- `taxonomy.yml` lists the initial controlled values for layers, disciplines,
  statuses, portability classes, and seed domains.
- `schema.v3.yml` defines the current lifecycle contract; `standard.md` is its companion guide.
- `schema.v2.yml` preserves the legacy field contract during migration.
- `examples/` contains v2 compatibility fixtures and v3 Markdown, YAML and
  supersession examples.

## Scripts

- `scripts/01.harness/artifact-metadata/check-headers/script.sh` is the
  capability-scoped entrypoint for metadata header checks.
- `scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh` proves compatibility, lifecycle validation and staged-content enforcement.
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh --batch <n>` applies one governed v2 backfill batch, validates it, commits it, records the chat commit, and checkpoints the session log.
- `scripts/01.harness/artifact-metadata/generate-index/script.sh` emits a JSON
  artifact index from v1/v2/v3 metadata headers, preserving lifecycle fields.
- `scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh` proves
  index generation preserves v3 lifecycle fields, v2 IDs and legacy v1 entries.
- `scripts/01.harness/artifact-metadata/update-lifecycle/script.sh` reports a
  bounded lifecycle migration or update; `--apply` writes the reviewed paths
  without staging or committing. Its smoke test covers provenance, transitions
  and idempotence. See its capability README for commands.

## Migration

The existing v1 metadata headers remain valid while the repo is incrementally
migrated. New and intentionally migrated artifacts use v3. Existing v1/v2 remain valid.
Use the lifecycle helper for date backfill; the older v2 batch script above
automatically commits and is not the lifecycle migration command.

Script metadata is in scope for v2 and v3. Existing `agentic-script` headers
remain valid during migration; versioned script artifacts include `kind: script` plus
script-specific `effects` validation.

The lifecycle decision is recorded in
`docs/01.harness/adrs/0038-track-artifact-lifecycle-dates.md`.
