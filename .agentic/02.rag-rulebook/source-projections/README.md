<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.source-projections.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: source-projection-registry
purpose: Define the source projection registry that maps approved source material to derived rulebook outputs.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.script.check-source-projections
  path: scripts/02.rag-rulebook/check-source-projections/script.sh
-->
# Source Projections

This directory records which approved source-material files are expected to
produce which structured rulebook outputs.

Source material remains the canonical human-authored corpus input. Structured
YAML rules are projections from that source material. The projection registry
keeps those relationships explicit enough for commit gates to detect added,
removed, moved, stale, or orphaned source-to-rule outputs.

The active manifest is:

`v1.yml`

