<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.migration-plan.prototype-corpus-domain-split
version: 1
status: active
layer: 02.rag-rulebook
domain: corpus
disciplines:
- agentic
- architecture
kind: migration-plan
purpose: Plan the governed split of the prototype docs/harness/architecture corpus into numbered domain corpus homes.
portability:
  class: internal
  targets: []
used_by:
- id: rag-rulebook.plan.repo
  path: .agentic/02.rag-rulebook/plans/repo-plan.md
- id: rag-rulebook.plan.prototype-corpus-migration-map
  path: .agentic/02.rag-rulebook/plans/prototype-corpus-migration-map.yml
- id: rag-rulebook.standard.domain-corpus-package
  path: .agentic/02.rag-rulebook/standards/domain-corpus-package.md
- id: harness.workflows.migrate-artifact-paths
  path: .agentic/01.harness/workflows/migrate-artifact-paths.md
-->
# Prototype Corpus Domain Split Migration Plan

## Purpose

Split the current prototype architecture corpus at `docs/harness/architecture`
into numbered domain corpus homes without losing source provenance, retrieval
coverage, rule graph edges, or compatibility for older references.

This plan authorizes planning only. Moving committed files, retiring old paths,
or adding compatibility pointers needs a follow-up implementation slice under
`.agentic/01.harness/workflows/migrate-artifact-paths.md`.

New document artifacts created during this migration must follow
`.agentic/01.harness/standards/document-artifact-placement.md` so the old
prototype corpus does not continue to grow while it is being split.

## Current State

`docs/harness/architecture` is the prototype corpus named by ADR 0022 and the
domain corpus package standard. It currently mixes:

- original and Markdown product architecture guides;
- product/platform/core source material;
- harness, chat, product, deploy, and rulebook ADRs;
- product, deploy, harness, and shared structured rules;
- product task rule packs;
- the platform runtime implementation plan.

The inventory map at
`.agentic/02.rag-rulebook/plans/prototype-corpus-migration-map.yml` remains the
file-level target inventory for this migration plan.

## Execution Status

- 2026-08-31 Slice 1 started execution. Initialized `docs/01.harness/`,
  `docs/03.product/`, and `docs/06.shared/` root READMEs; registered those
  roots with metadata, recognition, corpus-root, source-material, runtime,
  YAML, explanation-readiness, and retirement-reference checks; moved the
  platform runtime implementation plan to
  `.agentic/03.product/plans/implementation/platform-runtime-implementation.md`;
  and left a compatibility pointer at the old plan path.
- 2026-08-31 Slice 1 validation passed for metadata headers, recognition
  freshness, corpus-root changes, source projections, source-material coverage,
  derivation reports, rulebook index/chunk smoke checks, runtime freshness,
  explanation readiness, path-migration helpers, and focused selector fixtures.
  The full selector fixture matrix exceeded a 10-minute bounded run and should
  be treated as a separate performance/coverage follow-up before requiring it
  for every migration slice.
- 2026-08-31 Slice 2 started ADR migration. Added ADR 0032 to record
  owner-aligned ADR roots, updated the chat commit readiness gate to accept
  numbered ADR roots, added `docs/01.harness/adrs/` and
  `docs/03.product/adrs/` READMEs, and moved product-owned ADRs 0024, 0025,
  0026, 0027, and 0031 to `docs/03.product/adrs/` with old-path pointers.
- 2026-08-31 Slice 3 continued ADR migration. Initialized
  `docs/02.rag-rulebook/` plus `docs/02.rag-rulebook/adrs/` and
  `docs/04.deploy/adrs/` README artifacts; moved RAG/rulebook ADRs 0022,
  0023, and 0029 plus deploy ADRs 0016 and 0028 into owner-aligned ADR roots;
  updated active deploy evidence that cited ADR 0028; and left old-path
  compatibility pointers under the prototype ADR root.
- 2026-08-31 Slice 4 continued ADR migration. Added
  `docs/00.chat/adrs/` as the owner-aligned chat ADR root; moved chat-owned
  ADRs 0001, 0002, 0004, 0005, 0006, 0007, 0009, 0010, 0011, 0013, 0014,
  0019, and 0030; updated active chat/public/education references to the new
  paths; and left old-path compatibility pointers under the prototype ADR
  root.

## Target Homes

The migration should use physical repo paths that align with numbered layer
ownership, while preserving corpus IDs in metadata, source projections, indexes,
chunks, and selector fixtures.

| Content | Target home | Corpus owner |
| --- | --- | --- |
| Chat lifecycle ADRs and chat-owned docs currently in harness ADR history | `docs/00.chat/` | `corpus.00.chat` |
| Harness ADRs, harness rules, command-surface rules, and harness migration history | `docs/01.harness/` | `corpus.01.harness` |
| RAG/rulebook source material and rules about the RAG/rulebook system itself | `docs/02.rag-rulebook/` | `corpus.02.rag-rulebook` |
| Product, apps, packages/core, design-system, frontend-kit, platform, and product-runtime source/rules/rule packs | `docs/03.product/` | `corpus.03.product` and subcorpora |
| Deploy source material and deploy/runtime-operation rules | `docs/04.deploy/` | `corpus.04.deploy` |
| Education ADRs and teaching/publication source material | `docs/05.education/` or the existing `docs/education/` namespace until a separate namespace decision | `corpus.05.education` |
| Cross-layer concerns that are deliberately not product-only, deploy-only, or harness-only | `docs/06.shared/` | `corpus.06.shared` |

Prefer domain-owned `docs/<numbered-layer>/rules/**` for structured rulebook
YAML. `02.rag-rulebook` owns reusable machinery and its self-corpus; it should
not become the home for every product, deploy, or harness rule.

## Forward Placement During Migration

While this plan is active, do not add ordinary ADRs, guides, source material,
plans, rules, rule packs, or corpus docs under `docs/harness/architecture/**`.
The only allowed additions under that legacy root are approved compatibility
pointers, migration-plan updates, and reference-preserving edits required by a
governed execution slice.

Use the document artifact placement standard to choose a new artifact's owner
and path before creating it. If the correct numbered docs root does not exist
yet, create the root README, metadata allowlist support, and corpus wiring in
the same governed slice before placing content there.

## Reference Inventory

Planner output was collected on 2026-08-30 with
`scripts/01.harness/plan-artifact-path-migration.sh`.

| Old path | Example target path | Old refs | New refs | Notes |
| --- | --- | ---: | ---: | --- |
| `docs/harness/architecture` | split across numbered `docs/<layer>/` roots | 1229 | `docs/03.product`: 1 | Root split cannot be validated as one direct move. Use phased child-path migrations. |
| `docs/harness/architecture/guides` | `docs/03.product/source-material/guides` | 45 | 0 | Guides are product architecture source material; preserve originals with Markdown derivatives. |
| `docs/harness/architecture/source-material` | `docs/03.product/source-material` | 170 | 0 | Current files already project to `corpus.03.product.core` and `corpus.03.product.platform`. |
| `docs/harness/architecture/plans` | `.agentic/03.product/plans/implementation` | 21 | 1 | The platform runtime implementation plan is product governance, not corpus source material. |
| `docs/harness/architecture/rules` | split across `docs/01.harness`, `docs/03.product`, `docs/04.deploy`, `docs/06.shared` | 660 | `docs/03.product/rules`: 0 | Rules must move by owner corpus, not wholesale into `02.rag-rulebook`. |
| `docs/harness/architecture/rule-packs` | `docs/03.product/rule-packs` | 76 | 0 | Current rule packs are product task packs; move by subcorpus. |
| `docs/harness/architecture/adrs` | split across numbered decision roots | 239 | `docs/01.harness/adrs`: 0 | ADRs need classification by decision owner before moving. |

Active references appear in workflow, script, architecture, generated
recognition-source, source-projection, derivation-report, selector-fixture,
README, manifest, and product/deploy implementation evidence buckets.
`commitLogs/**` references are historical audit evidence and should not be
rewritten only to modernize paths.

## Compatibility Choice

Use `pointer` compatibility for the old prototype paths during the migration.

Pointer files should be human-readable Markdown indexes that say the prototype
corpus has split, list the new canonical roots, and link to this migration
plan. Do not use executable wrappers for docs. Avoid symlink aliases unless a
tool proves it must read the old directory directly.

Retire old path pointers only after:

- active old-path references outside the migration plan are gone;
- generated recognition sources point at canonical targets;
- source projections, derivation reports, and selector fixtures are updated;
- a fresh rulebook index proves all related rulesets and required rulesets
  resolve from canonical paths;
- local RAG runtime build, freshness, and query smoke checks pass.

## Target Mapping

Use the existing map for file-level details. These are the first physical path
families expected by that map:

- `docs/03.product/source-material/guides/markdown/`
- `docs/03.product/source-material/guides/originals/`
- `docs/03.product/source-material/core/`
- `docs/03.product/source-material/platform/`
- `.agentic/03.product/plans/implementation/`
- `docs/03.product/rules/apps/`
- `docs/03.product/rules/core/`
- `docs/03.product/rules/design-system/`
- `docs/03.product/rules/frontend-kit/`
- `docs/03.product/rules/platform/`
- `docs/03.product/rule-packs/apps/`
- `docs/03.product/rule-packs/core/`
- `docs/03.product/rule-packs/design-system/`
- `docs/03.product/rule-packs/platform/`
- `docs/04.deploy/rules/shared/` for deploy-owned infra rules
- `docs/01.harness/rules/` for harness-owned command-surface and harness rules
- `docs/06.shared/rules/` for truly cross-corpus concerns

The exact ADR split should be a first execution deliverable. Do not move ADRs
as a bulk directory until each ADR has an assigned decision owner and stable
target path.

## ADR Owner Classification

This table records the provisional target owner for prototype ADRs before
moving them. Move files in small batches and keep old-path pointer
compatibility until active references are updated.

| ADR | Owner | Target root | Status |
| --- | --- | --- | --- |
| 0001 Record Harness Session Decisions Before Commit | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0002 Clean Up Duplicate Chat Branches | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0003 Review Process Prose For Deterministic Gates | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0004 Group Chat Logs And Summarize Session Metrics | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0005 Preserve Bootstrap Dirty Worktree Before Workflow Loading | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0006 Use Session Metadata For Routing After Chat Start | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0007 Require Explicit Write Permission With Bookkeeping Exception | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0008 Add Education Layer | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0009 Use Isolated Worktrees For Session Commit Boundaries | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0010 Protect Commit Logs With Recorded Work | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0011 Use Chat-Owned Worktrees For Local Convergence | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0012 Treat Missing Governance As Stop Condition | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0013 Create Chat Layer And On-Demand Session Summary | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0014 Promote Reusable Lessons Upstream | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0015 Use Shared Upstream Repo Bootstrap Standard | `06.shared` | `docs/06.shared/adrs/` | pending |
| 0016 Add AWS Layer | `04.deploy` | `docs/04.deploy/adrs/` | moved in slice 3 |
| 0017 Organize Scripts By Owner, Domain, And Capability | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0018 Govern Artifact Path Migrations | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0019 Use Chat Docs Namespace | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0020 Use Scripts For Layer Command Surfaces | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0021 Use Versioned Artifact Metadata For Agent Navigation | `01.harness` | `docs/01.harness/adrs/` | pending |
| 0022 Add RAG/Rulebook Layer | `02.rag-rulebook` | `docs/02.rag-rulebook/adrs/` | moved in slice 3 |
| 0023 Require RAG Knowledge Disposition For Code Changes | `02.rag-rulebook` | `docs/02.rag-rulebook/adrs/` | moved in slice 3 |
| 0024 Use Translation-Ready Message Descriptors | `03.product` | `docs/03.product/adrs/` | moved in slice 2 |
| 0025 Place Composed Runtime Contexts In Platform Contracts | `03.product` | `docs/03.product/adrs/` | moved in slice 2 |
| 0026 Use App Mount As Platform Integration Boundary | `03.product` | `docs/03.product/adrs/` | moved in slice 2 |
| 0027 Use Provider Type Service Adapter Layout | `03.product` | `docs/03.product/adrs/` | moved in slice 2 |
| 0028 Use Client Environment Deployment Target Profiles | `04.deploy` | `docs/04.deploy/adrs/` | moved in slice 3 |
| 0029 Use Purpose And Authority Aware RAG Retrieval | `02.rag-rulebook` | `docs/02.rag-rulebook/adrs/` | moved in slice 3 |
| 0030 Require Formal Commit Readiness Gate Before Task Commits | `00.chat` | `docs/00.chat/adrs/` | moved in slice 4 |
| 0031 Use Products As App Composition Boundary | `03.product` | `docs/03.product/adrs/` | moved in slice 2 |
| 0032 Use Owner-Aligned ADR Roots | `01.harness` | `docs/01.harness/adrs/` | added in slice 2 |

## Ordered Execution Plan

1. Preflight the current prototype corpus.
   - Run the artifact path planner for every source/target pair in the slice.
   - Run artifact metadata header checks.
   - Generate and validate the current rulebook index.
   - Build the local RAG runtime and confirm freshness.
   - Confirm no task files are dirty except approved session bookkeeping.

2. Create target roots and README pointers.
   - Apply `.agentic/01.harness/standards/document-artifact-placement.md`
     before creating new document artifacts or numbered docs roots.
   - Add `docs/01.harness/`, `docs/03.product/`, and `docs/06.shared/`
     corpus READMEs before moving files into them.
   - Update artifact metadata header path allowlists so new numbered docs roots
     validate.
   - Add temporary pointer READMEs under old `docs/harness/architecture/**`
     roots only as each child path becomes empty.

3. Move the platform runtime implementation plan first.
   - Move `docs/harness/architecture/plans/platform-runtime-implementation-plan.md`
     to `.agentic/03.product/plans/implementation/platform-runtime-implementation.md`.
   - Preserve the stable artifact ID unless the plan is split.
   - Update `.agentic/03.product/workflows/platform-runtime-implementation.md`,
     deploy blueprints, AWS/deploy ADR references, recognition sources, and
     derivation reports.
   - Keep an old-path pointer until active references are gone.

4. Move product source material and guides.
   - Move product guides and original PDFs under `docs/03.product/source-material/guides/`.
   - Move `packages-core-contract-surface-v1.md` under product core source
     material.
   - Move `platform-runtime-enterprise-obligations-v1.md` and
     `platform-infra-capability-layering-v1.md` under product platform source
     material.
   - Update source projections, source-material coverage checks, derivation
     reports, selector fixtures, generated recognition sources, and runtime
     source roots together.

5. Move product rules and product rule packs by subcorpus.
   - Move packages/core rules and rule packs into the product core subcorpus.
   - Move platform runtime, adapter-consumption, config, events, persistence,
     identity/security, reporting/audit, notifications, and tenancy rules into
     the product platform subcorpus unless split review assigns deploy-owned
     pieces elsewhere.
   - Move apps, design-system, and frontend-kit rules/packs into matching
     product subcorpora.
   - Update all `related_rulesets`, `required_rulesets`, `used_by`, source
     derivation paths, source hashes where needed, and success criteria that
     name old paths.

6. Move deploy, harness, and shared rules.
   - Move `infra.yml` and deploy-specific rule edges into `docs/04.deploy/`.
   - Move `scripts-command-surface.yml` and harness-only process rules into
     `docs/01.harness/`.
   - Move only genuinely cross-corpus concerns into `docs/06.shared/`; otherwise
     split them per owner corpus with new stable artifact IDs.

7. Classify and move ADRs.
   - Assign every ADR to the layer that owns the decision, not merely the layer
     that triggered the conversation.
   - Keep historical `commitLogs/**` ADR references untouched.
   - Update public bootstrap exports and documentation that intentionally still
     cite selected ADRs.
   - Add or update an ADR for the corpus split before retiring the old ADR root,
     because this changes durable documentation layout.

8. Regenerate and validate retrieval surfaces.
   - Regenerate generated recognition sources.
   - Rebuild and validate rulebook indexes and chunks.
   - Run source projection, source material coverage, derivation report, and
     selector fixture checks for all affected corpora.
   - Run representative `query-local-context` checks for product, deploy,
     harness, and RAG/rulebook prompts.

9. Retire old paths.
   - Run `check-artifact-path-migration.sh --plan <this-plan> <old> <new>` for
     each direct move.
   - Use `--allow-active-old-path` only while pointer compatibility is approved.
   - Remove pointers only when active references outside historical session
     logs and this migration plan are gone.

## Required Checks

At minimum, each execution slice should run:

```bash
bash scripts/00.chat/worktree/dirty-worktree-check/script.sh --allow-session-bookkeeping
bash scripts/00.chat/worktree/check-write-location/script.sh
bash scripts/01.harness/smoke-test-artifact-path-migration.sh
bash scripts/01.harness/artifact-metadata/check-headers/script.sh --all
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
bash scripts/02.rag-rulebook/generate-rulebook-index/smoke-test.sh
bash scripts/02.rag-rulebook/generate-rulebook-chunks/smoke-test.sh
bash scripts/02.rag-rulebook/check-source-projections/script.sh --current
bash scripts/02.rag-rulebook/check-source-material-coverage/script.sh --current
bash scripts/02.rag-rulebook/validate-derivation-reports/script.sh --current
bash scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/script.sh --current
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh
bash scripts/02.rag-rulebook/check-runtime-freshness/script.sh
git diff --check
```

Also run a focused path-migration checker for each moved source/target pair.
For a split move, validate the concrete child paths rather than treating the
root as a one-to-one rename.

## Stop Conditions

Stop before moving files if:

- the source and target pair cannot be represented by a concrete migration
  slice;
- a target root collides with an existing incompatible path;
- an active old-path reference remains without a pointer or approved reference
  update;
- moving a rule breaks `related_rulesets` or rule-pack `required_rulesets`;
- moving source material breaks source projection, derivation report, selector
  fixture, generated recognition-source, or local runtime freshness checks;
- an ADR has ambiguous decision ownership;
- a cross-corpus concern cannot be safely kept shared or split with new stable
  artifact IDs.

## Recovery

If validation fails after a slice:

- revert only the files changed by that slice, preserving unrelated user work;
- leave old prototype files in place if references cannot be updated safely;
- restore pointer compatibility if a moved path is still used by tooling;
- regenerate recognition sources and rulebook indexes from the restored state;
- record the failed pair, old references, and next blocker in the session log.

## Completion Criteria

The migration is complete when:

- all prototype corpus content has a canonical numbered docs or agentic plan
  home;
- `docs/harness/architecture` is either absent or contains only an approved
  short compatibility pointer;
- active references outside this migration plan no longer require the old
  prototype path;
- metadata headers, source projections, derivation reports, selector fixtures,
  recognition sources, rulebook indexes, chunks, and local RAG runtime checks
  all pass;
- historical `commitLogs/**` references remain untouched as audit history.
