<!-- agentic-artifact:
schema: agentic-artifact/v2
id: harness.adrs.readme
version: 1
status: active
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

During the prototype corpus migration, older harness ADRs may remain under
`docs/harness/architecture/adrs/` until a governed path migration moves them
and leaves pointer compatibility.
