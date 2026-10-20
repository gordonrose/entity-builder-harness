<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.adr.0038-track-artifact-lifecycle-dates
version: 1
status: active
created_on: "2026-10-20"
updated_on: "2026-10-20"
layer: 01.harness
domain: metadata
disciplines: [agentic, architecture]
kind: adr
purpose: Record lifecycle dates and replacement links as a versioned artifact contract.
portability:
  class: source-only
  targets: []
used_by:
  - id: harness.capability.artifact-metadata
    path: .agentic/01.harness/artifact-metadata/README.md
-->
# 0038 Track Artifact Lifecycle Dates

Status: accepted
Date: 2026-10-20

## Context

V2 metadata identifies artifacts and their status, but cannot record creation,
last update, deprecation or supersession dates. Header comments also cannot
provide visible replacement navigation in rendered documents. Adding unchecked
fields would silently lose them from the artifact index, and added-file-only
commit checks would miss normal lifecycle edits.

## Decision

Introduce `agentic-artifact/v3` with required quoted UTC `created_on` and
`updated_on` dates, conditional `deprecated_on` and `superseded_on`, and ID-plus-path
`superseded_by` references. Keep v1/v2 readable during focused migration batches.
The existing semantic artifact `version` stays independent of schema version
and ordinary modification dates. The canonical contract and guide live in
`.agentic/01.harness/artifact-metadata/schema.v3.yml` and `standard.md`.

Use a default-report, explicit-apply helper for date maintenance and v2 migration.
Never automatically stage or commit a metadata backfill. Report Git provenance:
first observed repository addition is not proven original authorship. Unknown
creation or historical transition dates require explicit confirmation.

Validate staged content and replacement targets, including ordinary v3 changes,
without modifying the Git index. Require current dates for new changes and
preserve creation dates across renames. Preserve lifecycle fields in indexes and
generators. Superseded artifacts remain discoverable as history, with visible
replacement links for Markdown readers; they are not active RAG guidance.

## Consequences

Dates become useful independently of Git access, while precise history remains
in Git and migration reports. Day-level UTC dates deliberately omit time-of-day
precision. Comments require quoted dates to avoid YAML timestamp coercion.

A schema version permits strict lifecycle requirements without retroactively
invalidating all v2 files. Consumers must recognize v3 explicitly before migration;
unknown explicit schemas cannot masquerade as legacy metadata. Legacy artifacts
and generated v2 outputs may be migrated later in bounded, reviewed batches.

This decision extends ADR 0021; it does not retire the stable-ID or versioning
policy, or authorize deletion of superseded files.
