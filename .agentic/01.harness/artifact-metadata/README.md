<!-- agentic-artifact:
owner: harness
kind: readme
purpose: Index the harness artifact metadata capability, including the v2 schema, taxonomy, and future index generator.
domain: metadata
portability: llm-workbench-required
used_by:
  - .agentic/01.harness/README.md
  - .agentic/01.harness/workflows/change-harness.md
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
