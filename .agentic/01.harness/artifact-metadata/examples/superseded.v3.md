<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.example.artifact-metadata.superseded-v3
version: 1
status: superseded
created_on: "2026-10-20"
updated_on: "2026-10-20"
deprecated_on: "2026-10-20"
superseded_on: "2026-10-20"
superseded_by:
  - id: harness.example.artifact-metadata.markdown-v3
    path: .agentic/01.harness/artifact-metadata/examples/markdown.v3.md
layer: 01.harness
domain: metadata
disciplines: [agentic, architecture]
kind: example
purpose: Show a superseded artifact with a resolvable replacement.
portability:
  class: reusable
  targets: [llm-workbench, entity-builder, design-system-builder]
used_by:
  - id: harness.capability.artifact-metadata
    path: .agentic/01.harness/artifact-metadata/README.md
-->
# Superseded V3 Metadata Example

Superseded by [Markdown V3 Metadata Example](markdown.v3.md).

This fixture demonstrates a historical artifact that remains discoverable by ID
and directs readers to its replacement. It is not active guidance.
