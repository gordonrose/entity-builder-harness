<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.capability.artifact-metadata
version: 1
status: active
layer: 01.harness
domain: metadata
disciplines:
  - agentic
kind: readme
purpose: Index the harness artifact metadata capability, including the v2 schema, taxonomy, and index generator.
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

- `standard.md` defines the preferred `agentic-artifact/v2` metadata shape,
  versioning policy, stable artifact IDs, and ID-first references.
- `taxonomy.yml` lists the initial controlled values for layers, disciplines,
  statuses, portability classes, and seed domains.
- `schema.v2.yml` records the v2 field contract in machine-readable form for
  future checker and index-generator work.
- `examples/` contains minimal v2 Markdown and YAML fixtures used to keep the
  checker behavior concrete.

## Scripts

- `scripts/01.harness/artifact-metadata/check-headers/script.sh` is the
  capability-scoped entrypoint for metadata header checks.
- `scripts/01.harness/artifact-metadata/check-headers/smoke-test.sh` proves the
  checker accepts v1 and v2 headers and rejects a generated missing-header
  fixture.
- `bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh --batch <n>` applies one governed v2 backfill batch, validates it, commits it, records the chat commit, and checkpoints the session log.
- `scripts/01.harness/artifact-metadata/generate-index/script.sh` emits a JSON
  artifact index from v1 and v2 metadata headers.
- `scripts/01.harness/artifact-metadata/generate-index/smoke-test.sh` proves
  index generation includes v2 IDs and legacy v1 entries.

## Migration

The existing v1 metadata headers remain valid while the repo is incrementally
migrated. New or materially changed artifacts should prefer the v2 schema.

Script metadata is in scope for v2. Existing `agentic-script` headers remain
valid during migration, and v2 script artifacts must include `kind: script` plus
script-specific `effects` validation.
