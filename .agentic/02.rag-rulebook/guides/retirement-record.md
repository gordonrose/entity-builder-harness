<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.guide.retirement-record
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: guide
purpose: Teach how retirement records preserve source, rule, and runtime lineage when governed RAG artifacts are removed or superseded.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.retirement-record
  path: .agentic/02.rag-rulebook/schemas/retirement-record.schema.yml
- id: rag-rulebook.retirements.readme
  path: .agentic/02.rag-rulebook/retirements/README.md
- id: rag-rulebook.script.validate-retirement-records
  path: scripts/02.rag-rulebook/validate-retirement-records/script.sh
-->
# Retirement Record Guide

## Mental Model

A retirement record is the receipt for removing knowledge from the active RAG
system.

Source material, YAML rules, chunks, indexes, recognition sources, and
evaluation fixtures can all shape retrieval. If one disappears, the system
needs to know whether that was intentional, what replaced it, and whether any
active reference still points at the old path.

The record does not keep the retired content alive. It keeps the decision
auditable.

## What Good Looks Like

Good retirement records:

- name each retired repo path
- record the prior SHA-256 hash for each retired artifact
- say whether the path was removed, renamed, superseded, or retained retired
- name replacement paths when the knowledge moved
- list the roots that were searched for remaining references
- keep accepted retirements free of active references to retired paths
- include validation commands and review decision

## What Bad Looks Like

Bad retirement records:

- say an artifact was retired but omit the previous hash
- leave a renamed artifact without a replacement path
- accept a retirement while active rules still reference the old source
- use `accepted` status while review remains pending
- remove a source file without checking derived rules, chunks, selectors, and
  projection records
- rely on commit history alone as the explanation

## How Agents Should Use It

Before deleting or superseding governed RAG material, an agent should decide
whether the change is a retirement.

If it is a retirement:

- create or update a retirement record
- record the previous artifact hash before deletion
- update source projections, derivation reports, rules, indexes, chunks, and
  evaluations as needed
- run the retirement validator and the RAG commit gate

If the artifact is merely being edited in place, do not create a retirement
record. Use source provenance, derivation reports, and runtime freshness checks
instead.
