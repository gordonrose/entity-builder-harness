<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.retirements.readme
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: guide
purpose: Explain where governed RAG/rulebook retirement records live and when to add one.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.retirement-record
  path: .agentic/02.rag-rulebook/schemas/retirement-record.schema.yml
- id: rag-rulebook.guide.retirement-record
  path: .agentic/02.rag-rulebook/guides/retirement-record.md
- id: rag-rulebook.script.validate-retirement-records
  path: scripts/02.rag-rulebook/validate-retirement-records/script.sh
-->
# Retirement Records

This directory stores governed records for RAG/rulebook artifacts that are
removed, renamed, superseded, or intentionally retained in a retired state.

Use a retirement record when active RAG inputs or outputs stop being active:

- source material
- structured rules
- rule packs
- derivation reports
- corpus gaps
- recognition sources or candidates
- selector evaluations
- generated indexes, chunks, or runtime caches
- workflows or scripts that control RAG behavior

Do not use retirement records for normal edits. Normal edits should be handled
by source hashes, derivation reports, generated output freshness, and commit
gates.

## Required Proof

Accepted retirement records must prove:

- each retired artifact has a prior SHA-256 hash
- removed, renamed, or superseded paths are absent after retirement
- retained retired paths still exist
- replacements exist when the artifact was renamed or superseded
- active references to the retired paths have been checked and cleared
- validation checks ran and no retirement checks are pending
- human review accepted the retirement
