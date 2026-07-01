<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.guide.source-projection-manifest
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: guide
purpose: Teach how source projection manifests keep source material, YAML rules, reports, and retrieval proof aligned.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.source-projection-manifest
  path: .agentic/02.rag-rulebook/schemas/source-projection-manifest.schema.yml
- id: rag-rulebook.script.check-source-projections
  path: scripts/02.rag-rulebook/check-source-projections/script.sh
-->
# Source Projection Manifest Guide

## Mental Model

Think of source material as the book, and structured YAML as the index cards
made from that book.

The source projection manifest answers:

- Which source page is canonical?
- Which YAML cards should exist because of it?
- Which derivation report explains the interpretation?
- Which selector fixtures prove the cards can be retrieved or safely blocked?

The manifest does not replace semantic review. It makes the mechanical contract
checkable.

## What Good Looks Like

A good projection set names one bounded source topic and the exact derived
outputs expected from it.

Good projection sets:

- name existing Markdown source material
- name the owning corpus and layer
- name every derived YAML rule
- name the derivation report
- name known corpus gaps when work is incomplete
- name retrieval selector evaluations that prove behavior
- keep hashes in derived YAML provenance current

## What Bad Looks Like

Bad projection sets:

- leave a source file undeclared
- point at a deleted source file
- list YAML that does not exist
- list YAML that lacks `source_derivation`
- let a YAML projection reference a source file not named in the manifest
- rely on a derivation report that does not mention the source
- treat a selector fixture as proof when the fixture file does not exist

## How Agents Should Use It

When source material changes, an agent should check the manifest before editing
derived YAML.

If a source file is new, add a projection set or a governed corpus gap.

If a source file is removed, update or retire the projection set and check
references.

If derived YAML changes, make sure the source material and derivation report
still explain it.

If a prompt should retrieve the new knowledge, add or update selector
evaluation proof.

