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

## Scripts

- `scripts/01.harness/artifact-metadata/check-headers/script.sh` is the
  capability-scoped entrypoint for metadata header checks. During migration it
  delegates to the existing compatibility checker at
  `scripts/01.harness/check-artifact-metadata-headers.sh`.

## Migration

The existing v1 metadata headers remain valid while the checker and repo are
incrementally migrated. New or materially changed artifacts should prefer the
v2 schema once the checker supports it.

Script metadata is in scope for v2. Existing `agentic-script` headers remain in
place until the checker supports structured v2 parsing and script-specific
`effects` validation.
