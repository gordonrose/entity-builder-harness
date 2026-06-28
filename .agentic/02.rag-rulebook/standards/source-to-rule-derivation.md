<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.standard.source-to-rule-derivation
version: 1
status: active
layer: 02.rag-rulebook
domain: rulebook
disciplines:
- agentic
- architecture
kind: standard
purpose: Define how approved source material becomes structured rules while preserving drift and conflict review.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.schema.source-to-rule-derivation-report
  path: .agentic/02.rag-rulebook/schemas/source-to-rule-derivation-report.schema.yml
- id: rag-rulebook.workflow.derive-rules-from-source
  path: .agentic/02.rag-rulebook/workflows/derive-rules-from-source.md
- id: rag-rulebook.derivation-reports.readme
  path: .agentic/02.rag-rulebook/derivation-reports/README.md
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
-->
# Source-To-Rule Derivation

## Purpose

Define the governed path from approved corpus source material to structured
rules, rule packs, indexes, chunks, and retrieval evaluations.

The goal is not to let an LLM freely rewrite rulebooks. The goal is to let an
agentic pipeline propose semantic changes, record its reasoning, and then make
every durable output structured, reviewable, reproducible, and testable.

## Core Rule

Source material may be human-authored and approved as prose.

Structured rulebook outputs must still pass a derivation review before they are
treated as retrieval-ready knowledge.

Structured rulebook outputs derived from governed source material must carry a
top-level `source_derivation` block. The block records the derivation workflow,
derivation report, generator identity, generated timestamp, source material
paths, and source SHA-256 hashes. Commit gates recompute the source hashes and
fail when a YAML projection was derived from stale source material.

Each active source-to-rule relationship must also be declared in the active
source projection manifest. The manifest records the approved source files,
expected YAML projections, derivation reports, corpus gaps, selector
evaluations, and checks that prove the projection is current. Commit gates
must fail when source files, YAML projections, or derivation reports are added,
moved, removed, or orphaned without updating that registry.

The derivation review must ask:

- What source claims changed?
- Which existing rules, rulesets, chunks, fixtures, or gaps are affected?
- Does the source contradict existing rulebook material?
- Does it make older guidance stale, weaker, broader, or incomplete?
- Does it introduce terms that need recognition-source or candidate review?
- Which generated artifacts must be rebuilt?
- Which retrieval evaluations prove the new behavior?

Before semantic YAML changes are drafted, a source-to-rule work order should be
generated from the active source projection manifest. The work order is not a
derivation report and does not approve semantic changes. It is the deterministic
handoff packet that names the current source hashes, source outline, expected
rule paths, derivation report state, corpus gaps, selector proof paths, required
checks, and narrow next actions.

When an agent needs to propose actual semantic edits, generate a source-to-rule
draft packet from the work order. The draft packet may include bounded source,
current YAML, derivation report, corpus-gap, and selector-evaluation content so
the agent does not re-discover context or omit required evidence. The draft
packet is still read-only evidence; it is not permission to write files or
approve derivation.

## Required Derivation Report

Every non-trivial source-material change that creates, updates, removes, or
reorganizes rulebook knowledge should produce a source-to-rule derivation
report.

The report lives under:

`.agentic/02.rag-rulebook/derivation-reports/`

Use corpus subdirectories when helpful, for example:

`.agentic/02.rag-rulebook/derivation-reports/04.deploy/`

The report is not the source material and is not the rulebook. It is the audit
record that explains how source material became proposed rulebook changes.

## Drift And Conflict Review

Derivation review must search for two failure modes:

- **Conflict**: the new source says something incompatible with existing
  governed material.
- **Drift**: the new source changes meaning, scope, or required behavior enough
  that existing rules, chunks, fixtures, or recognition terms may now be stale.

Conflict examples:

- A new source says remote RAG must not read local files, while an older rule
  says the deployed service may inspect the repo directly.
- A deploy source says AWS mutation is banned during planning, while a rule
  allows planning prompts to trigger deployment tooling.

Drift examples:

- A source adds rollback as mandatory, but existing deploy rules do not mention
  rollback.
- A source narrows `MCP server` to a read-only context service, but existing
  fixtures still treat it as a generic deployment term.
- A rule changes corpus ownership but generated chunks still point at the old
  corpus.

When conflict or drift is suspected, the report must keep the issue visible.
The agent may propose a resolution, but it must not silently collapse the
difference.

## Outcome Rules

Use `needs-review` when semantic derivation is written but not approved.

Use `accepted` only when the report names the source changes, affected
artifacts, conflict review, drift review, proposed updates, validation results,
and reviewer decision.

<!-- deterministic-check: allow reason="derivation acceptance requires semantic and human review until a derivation-report validator and review helper exist" -->
Use `blocked` when conflict, ownership uncertainty, missing source approval, or
missing validation prevents safe downstream updates.

Use `superseded` when a later report replaces the report. The superseded report
must name the replacement.

## Good Actions

- Compare changed source material with existing rules before writing new rules.
- Generate a source-to-rule work order before asking an agent to draft or
  revise source-derived YAML.
- Generate a source-to-rule draft packet when the agent needs source and
  current-artifact content to propose semantic changes.
- Name affected rules, rule packs, corpus gaps, recognition candidates, chunks,
  and selector fixtures.
- Preserve source paths and evidence paths.
- Preserve source hashes in `source_derivation.source_material`.
- Register active source-to-rule relationships in the source projection
  manifest.
- Prefer narrow rule updates over broad rewrites.
<!-- deterministic-check: allow reason="missing-knowledge triage is human-governed until source derivation reports have validator support" -->
- Create review candidates or corpus gaps when knowledge is missing.
- Mark generated indexes, chunks, and evaluations stale until they are rebuilt
  and proven.
- Stop on unresolved conflict instead of guessing.

## Banned Actions

Do not:

- treat source material as retrieval-ready rulebook coverage by itself
- let an LLM rewrite rules without a derivation report
- hide contradictions behind a polished summary
- mark chunks or selector evaluations current when they were not regenerated
- update source material without regenerating or revalidating derived YAML
  provenance
- add or keep source-derived YAML that is not declared in the source projection
  manifest
- merge domain corpora to avoid ownership decisions
- accept semantic drift as harmless without naming affected artifacts
- publish or deploy a corpus package with unresolved blocking derivation gaps

## Automation Boundary

Future sub-agents may perform derivation work, but they must output a governed
report before durable rulebook changes are accepted.

Scripts should enforce shape, source hash freshness, generated-artifact drift,
and fixture results. LLM-assisted agents may help identify semantic claims,
conflicts, and drift, but their conclusions must be written as structured
report data.
