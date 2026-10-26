<!-- agentic-artifact:
schema: agentic-artifact/v3
id: harness.migration-plan.retire-rag-rulebook-layer
version: 1
status: superseded
created_on: "2026-10-26"
updated_on: "2026-10-26"
superseded_on: "2026-10-26"
superseded_by:
- id: harness.migration-plan.quarantine-rag-rulebook-layer
  path: .agentic/01.harness/plans/migration/quarantine-rag-rulebook-layer.md
layer: 01.harness
domain: migration
disciplines:
- agentic
- architecture
- sre
kind: migration-plan
purpose: Retire the current RAG/rulebook layer while preserving domain knowledge, provenance, and reusable non-retrieval safeguards.
portability:
  class: internal
  targets: []
used_by:
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
-->
# Retire the RAG/Rulebook Layer

> Superseded by [harness.migration-plan.quarantine-rag-rulebook-layer](quarantine-rag-rulebook-layer.md).


Superseded by [Quarantine the RAG/Rulebook Layer](quarantine-rag-rulebook-layer.md).

## Decision

Retire the current RAG/rulebook implementation after extracting or preserving
the durable knowledge and safeguards that the repository still needs. The
retirement removes the runtime, retrieval, indexing, prompt recognition,
context-packet, and RAG-specific validation model. It does not discard
owner-aligned product, deploy, harness, chat, or shared source material and
rules merely because RAG once indexed or derived them.

The target state has no active dependency on `.agentic/02.rag-rulebook/`,
`scripts/02.rag-rulebook/`, `docs/02.rag-rulebook/`, or
`infra/04.deploy/02.rag-rulebook/`. The numeric `02` layer is intentionally
left vacant for a future foundation-led design; the repository is not
renumbered as part of this migration.

## Scope And Baseline

The inventory was prepared from commit `3db60130` on 2026-10-26. It found:

| Path family | Tracked files | Initial disposition |
| --- | ---: | --- |
| `.agentic/02.rag-rulebook/` | 200 | retire after preserving migration evidence and owner records |
| `scripts/02.rag-rulebook/` | 104 | retire or replace by a non-RAG owner-specific check |
| `docs/02.rag-rulebook/` | 14 | archive as historical evidence or relocate durable non-RAG content |
| `infra/04.deploy/02.rag-rulebook/` | 11 | retire with the already retired service target |

There are 84 non-session-history files with active references to one or more
RAG paths: 17 governance files, 19 scripts, 41 domain-doc files, five deploy
files, and two root files. These references are active migration work, not
permission to retain the RAG layer.

## Disposition Inventory

### Retire: retrieval implementation

Retire the local HTTP service, local runtime cache, index and chunk generation,
context-packet schemas and validation, retrieval policy compilation, prompt
recognition sources and candidates, retrieval selector evaluations, query
commands, service-image commands, and `rag:*` package commands. They form one
delivery system and have no direct application, `packages/core`, or `platform`
runtime consumer.

Retire the hosted-service deployment tombstone, its inactive workflow, the RAG
image and ECS/Fargate configuration, and the deployment-readiness validator
once their historical evidence is safely recorded. The hosted target is already
retired; this migration must not reactivate it.

### Preserve with current owners: domain knowledge

Keep product, platform, deploy, chat, harness, and shared source material,
structured rules, rule packs, ADRs, and plans in their existing owner-aligned
directories. Their value is independent of retrieval. Examples include the
product package-documentation and untrusted-input rules, platform-layer rules,
and deploy container and platform-shell rules.

The 15 owner-aligned rules that currently name RAG derivation paths require
provenance migration before RAG records can be removed: five product rules,
seven RAG-named deploy rules, two deploy platform rules, and one shared deploy
rule. The future owner of each record is the rule's existing owner, not a new
central knowledge layer.

### Extract or replace: evidence safeguards

Evaluate each of these independently before retaining it:

- Source review records: eight records currently live under the RAG layer
  (three product, three deploy, one product-platform, one RAG). Preserve the
  accepted review evidence beside the source owner when it is still useful.
- Derivation reports: fourteen reports (six product or product-core/platform,
  five deploy, three RAG). Preserve a compact provenance record only when a
  current rule still relies on it; otherwise archive it as migration evidence.
- Corpus gaps: five records. Move unresolved product or deploy gaps to their
  owner if they still describe unimplemented work; close or archive RAG-only
  gaps.
- Retirement evidence: preserve the ability to retire governed artifacts with
  prior hashes and reference checks. Decide whether this belongs in the shared
  migration standard or owner-specific retirement records; it must not retain a
  RAG-only schema or validator by default.
- Source-to-rule coverage checks: retain only a minimal owner-neutral
  provenance check if it prevents a real, current defect. Remove requirements
  that only prove indexing, chunks, retrieval selection, or context packets.
- Code-change knowledge disposition: replace the RAG-named session-log gate
  with a narrower documentation/provenance decision only if the owning
  product and platform workflows still need it.

### Preserve for a future rebuild: bounded archive

Preserve a Git tag or recorded commit reference, this migration plan, and a
short rebuild brief capturing the useful ideas: owner-aligned source material,
explicit provenance, deterministic selection evaluations, stale-data checks,
and the service's security boundaries. Preserve representative failure fixtures
as historical examples only when they explain a future requirement; do not keep
their runtime or validator alive.

## Active Dependency Buckets

| Bucket | Current consumers | Required outcome |
| --- | --- | --- |
| Routing and chat classification | `AGENTS.md`, routing policy, task classifier, task fixtures | remove RAG as an active layer and route future retrieval requests to normal discovery/planning until a new design exists |
| Harness placement and terminology | harness README, manifest, terminology, placement and evaluation standards | replace RAG-owned definitions and corpus requirements with owner-aligned documentation rules |
| Commit selection and gates | repository check catalog, commit hook, chat commit preparation | remove RAG-specific selected checks; keep the generic selector and artifact metadata checks |
| Product and deploy provenance | domain rules, source material, owner READMEs | relocate or simplify records so rules retain valid owner-local provenance |
| Deployment history | AWS workflow, inactive GitHub workflow, RAG infrastructure and readiness manifests | retain a concise retirement record, then remove inactive executable surfaces |
| Public/bootstrap material | workbench export and portability scripts | remove RAG assumptions from exports and keep portable chat bootstrap independent |

## Compatibility Choice

The final disposition for all four RAG paths is `retired`, with no compatibility
wrapper or path alias. Historical session logs remain untouched. This plan is
the active migration evidence and is intentionally outside the retiring layer.

No RAG path may be deleted until all active references are removed or replaced.
The migration checker must be run separately for:

```text
.agentic/02.rag-rulebook
scripts/02.rag-rulebook
docs/02.rag-rulebook
infra/04.deploy/02.rag-rulebook
```

## Ordered Implementation Slices

1. Decide and move owner-local provenance, review evidence, gaps, and any
   retained validation outside the RAG layer. Validate each owner surface.
2. Remove RAG dependencies from routing, placement standards, commit selection,
   package commands, and public bootstrap material.
3. Retire the RAG service, scripts, evaluation suite, provider configuration,
   self-corpus, and deployment artifacts. Add one durable retirement record
   outside the retired namespace that links to the final pre-retirement commit.
4. Run path-migration checks, generic artifact metadata checks, affected product
   and deploy checks, and a repository-wide search proving active references
   are gone.

## Validation And Recovery

Each implementation slice must run its owner workflow checks plus the four
`check-artifact-path-migration.sh` checks for the retiring path families, with
this plan passed through `--plan`. Run artifact-header validation for this plan
and all affected owner records.

Before destructive slices, create an explicit Git tag or record the final
pre-retirement commit in the retirement evidence. Recovery is a revert of the
retirement commit or a rebuild from that recorded revision; no compatibility
path is promised.

## ADR Disposition

An ADR is required before deletion because this changes the durable repository
layer layout, removes public package commands, and ends a compatibility model.
The ADR should be created in `docs/01.harness/adrs/` before the first removal
slice and reference this plan.
