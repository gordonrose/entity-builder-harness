<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.adrs.readme
version: 1
status: active
created_on: "2026-08-31"
updated_on: "2026-10-20"
layer: 01.harness
domain: architecture
disciplines:
- agentic
- architecture
kind: adr-readme
purpose: Define the owner-aligned ADR home for harness-layer architecture decisions.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: harness.adr.0032-use-owner-aligned-adr-roots
  path: docs/01.harness/adrs/0032-use-owner-aligned-adr-roots.md
- id: harness.standards.document-artifact-placement
  path: .agentic/01.harness/standards/document-artifact-placement.md
-->
# 01.harness ADRs

This directory records durable architecture decisions owned by the harness
layer: workflows, gates, artifact metadata, document placement, command
surfaces, and repo-level agent governance.

Use this root for harness-owned ADRs that are corpus history. Agent-facing
workflow, standard, checklist, gate, and policy artifacts stay under
`.agentic/01.harness/`.

The old prototype ADR pointers have been retired. Use this owner-aligned ADR
root directly for harness-owned decision history.

## Artifact Metadata Decisions

- [0021: Versioned metadata](0021-use-versioned-artifact-metadata-for-agent-navigation.md)
- [0038: Lifecycle dates and supersession](0038-track-artifact-lifecycle-dates.md)
