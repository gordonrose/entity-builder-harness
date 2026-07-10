<!-- agentic-artifact:
schema: agentic-artifact/v2
id: rag-rulebook.plan.artifact-metadata-retrieval-profile-migration
version: 1
status: active
layer: 02.rag-rulebook
domain: retrieval
disciplines:
- agentic
- architecture
kind: plan
purpose: Track the migration from header coverage to generated retrieval profiles so RAG can proactively select the right repo context.
portability:
  class: reusable
  targets:
  - llm-workbench
  - entity-builder
  - design-system-builder
used_by:
- id: rag-rulebook.readme
  path: .agentic/02.rag-rulebook/README.md
- id: harness.artifact-metadata.generate-index
  path: scripts/01.harness/artifact-metadata/generate-index/script.sh
- id: rag-rulebook.script.generate-rulebook-index
  path: scripts/02.rag-rulebook/generate-rulebook-index/script.sh
-->
# Artifact Metadata Retrieval Profile Migration

## Goal

Make RAG retrieval proactive without manually adding RAG-specific hints to every
artifact header.

The target model is:

`agentic-artifact/v2 header -> artifact metadata index -> generated recognition
sources -> generated retrieval profiles -> profile chunks -> validated context
packets`

Headers remain the human-authored governance and identity contract. Retrieval
profiles are generated from those headers, paths, neighboring artifacts, and
known script roles.

## Ownership

- `01.harness` owns `agentic-artifact/v2` metadata shape, validation, backfill,
  and the artifact metadata index.
- `02.rag-rulebook` owns recognition sources, retrieval profiles, chunks,
  selector behavior, context packets, and RAG evaluations.
- If a field is useful outside RAG, add it to the artifact metadata standard.
- If a field is only a retrieval hint, derive it in RAG-owned generators.

## Current Baseline

Recorded from the active migration branch on 2026-07-10.

- `backfill-v2-headers --status`: `v2=678 legacy=0 missing=0`
- `check-headers --all`: `693` files passed after scope alignment,
  coverage-report command addition, and LLM audit report addition
- strict artifact index: `693` artifacts, `693` v2, `0` skipped, `0`
  duplicate IDs
- v2-headered files outside strict index: `0`
- generated recognition sources: refreshed after LLM audit report addition
- local RAG runtime build: passing
- retrieval selector fixture smoke: passing
- query-local-context smoke: passing

The `673` and `688` counts differ because `backfill-v2-headers --status`
counts `.agentic`, `docs`, and `scripts` files with `.md/.yml/.yaml/.sh`
suffixes, while the strict index also includes `.github`, `infra`, and
JS/MJS artifacts that are valid indexed artifacts.

## Completed Slices

### 1. Example Context Deprioritization

Status: complete in current branch, pending commit.

The selector now treats paths and artifact IDs inside phrases such as `e.g.`,
`i.e.`, and `for example` as illustrative context rather than primary target
paths.

Validation:

- illustrative example-path fixture passes
- full selector fixture smoke passes
- query-local-context smoke passes

### 2. Generated Retrieval Profiles

Status: complete in current branch, pending commit.

The rulebook index now emits generated `retrieval_profile` data for known
harness and RAG process sources. The chunk generator renders those as
`retrieval-profile` chunks.

The selector has question frames for:

- `question-frame.indexed-for-rag`
- `question-frame.rag-index-selection`

These frames promote generated profile chunks before final trimming.

Validation:

- generated-profile harness indexing fixture passes
- generated-profile RAG index selection fixture passes
- full selector fixture smoke passes

### 3. Artifact Index Scope Alignment

Status: complete in current branch, pending commit.

The artifact metadata checker and indexer now include:

- `docs/04.deploy`
- `docs/aws`
- `docs/education`
- YAML fixtures under `scripts/`

This closed the gap where v2-headered artifacts existed but did not enter the
strict artifact index.

Validation:

- `check-headers --all`: `688` files passed
- strict artifact index: `688` artifacts, `0` skipped, `0` duplicate IDs
- v2-headered but not indexed: `0`
- generated recognition sources refreshed and valid

## Remaining Migration Slices

### 4. Read-Only Profile Coverage Report

Status: complete in current branch, pending commit.

Added `scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/`.
The command audits every indexed artifact for derivable retrieval profile
coverage without reading source bodies as authority and without mutating files.

The report should classify each artifact as:

- `strong`: enough metadata exists to derive useful retrieval roles
- `partial`: enough metadata exists for identity but not process-role inference
- `weak`: retrieval needs source body or manual review to infer role
- `excluded`: intentionally not a retrieval target

Suggested output fields:

- artifact id and path
- layer, domain, kind, purpose
- derived roles
- derived `answers_questions_about`
- derived `produces`
- derived `consumes`
- derived `validates`
- confidence
- missing signals
- suggested source of repair: header, path convention, generator rule, or
  recognition candidate

Success criteria:

- report is read-only
- report covers all strict-index artifacts
- report produces machine-readable JSON
- report has a human summary
- no artifact is silently skipped

Failure criteria:

- report requires network or embeddings
- report mutates headers
- report treats body-text guessing as authoritative
- report cannot distinguish header weakness from generator weakness

Current report result after LLM-calibrated deterministic reporter updates,
audit-report addition, readme/agent/recognition-source derivation, and final
kind-contract derivation:

- artifacts: `693`
- `strong`: `692`
- `partial`: `0`
- `weak`: `0`
- `excluded`: `1`
- repair sources: `none=693`

Interpretation:

- Header identity coverage is healthy.
- No current artifact requires immediate header repair to become minimally
  retrievable.
- The deterministic coverage report has no remaining `partial` or `weak`
  indexed artifacts.
- The LLM calibration audit converted stable findings into deterministic rules
  for service artifacts, templates, configs, and rubrics without editing
  authored headers.
- The next deterministic derivation slice converted stable readme-like,
  ADR, agent, recognition-source, and source-material kinds without editing
  authored headers.
- The final deterministic derivation slice converted the remaining stable
  kind contracts for docs, examples, checklists, corpus gaps, plans, prompts,
  review records, rulesets, state records, skill/index records, and related
  governance records without editing authored headers.

Validation:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/check-headers/script.sh --all
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/generate-index/script.sh --all --pretty --strict >/tmp/artifact-index.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/script.sh --index /tmp/artifact-index.json --pretty
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/report-artifact-retrieval-profile-coverage/smoke-test.sh
```

### 5. LLM Calibration Audit

Status: complete in current branch, pending commit.

Added
`.agentic/02.rag-rulebook/evaluations/retrieval-profile-coverage/2026-07-10-llm-audit.md`.

The audit compared a stratified sample of `strong`, `partial`, and `excluded`
coverage records against actual artifact bodies. It found that the script is
strong enough as a migration triage tool, but not a complete semantic proof.

Findings converted into deterministic reporter rules:

- removed noisy `rulebook -> script.rule` action inference
- added service/server/http `serve` action inference
- derived service runtime production and request/runtime-boundary validation
- derived template, config, and rubric contracts from artifact kind

Result:

- `strong`: `545` -> `579`
- `partial`: `146` -> `112`
- `weak`: `0` -> `0`
- authored header edits: `0`

After the audit report itself was added as a metadata-bearing artifact, the live
branch result is `693` artifacts, `580` strong, `112` partial, `0` weak, and
`1` excluded.

### 6. Improve Deterministic Profile Derivation

Status: complete in current branch, pending commit.

Use the coverage report to improve generated profile derivation before changing
headers.

Preferred derivation inputs:

- `kind`
- `purpose`
- `domain`
- `layer`
- `disciplines`
- `used_by`
- `effects`
- path conventions
- sibling README files
- script directory names
- rulebook source references

Avoid one-off prompt terms unless they become recognition candidates or
evaluation fixtures.

Success criteria:

- fewer `partial` and `weak` artifacts without manual header edits
- generated profiles remain deterministic
- selector fixtures continue to pass

Completed deterministic derivations:

- readme-like artifacts now produce governed navigation and ownership guides
  and validate repository navigation and ownership expectations
- ADRs now produce architecture decision records and validate architecture
  decision rationale
- agent contracts now produce agent role contracts and validate agent
  responsibility boundaries
- recognition sources now produce recognition vocabulary sources and validate
  recognition term mapping expectations
- source material now produces source coverage for rule derivation and
  validates source-to-rule coverage expectations
- checklists now produce review checklists and validate checklist review
  expectations
- corpus gaps now produce corpus coverage gap records and validate gap tracking
  expectations
- docs now produce governed documentation artifacts and validate documentation
  accuracy expectations
- examples now produce worked example artifacts and validate example
  conformance expectations
- indexes now produce artifact family indexes and validate navigation
  expectations
- layer rulesets, rulesets, and rule packs now produce governed rule contracts
  and validate rule expectations
- migration plans and plans now produce tracking plans and validate progress
  expectations
- prompts now produce reusable prompt contracts and validate prompt usage
  expectations
- retirement records now produce artifact retirement records and validate
  retirement decision expectations
- review records now produce review evidence records and validate review
  evidence expectations
- skills now produce reusable model procedures and validate skill execution
  expectations
- state artifacts now produce governed state records and validate state
  tracking expectations

Result:

- `strong`: `580` -> `692`
- `partial`: `112` -> `0`
- `weak`: `0` -> `0`
- authored header edits: `0`

Remaining partial or weak artifacts: `0`.

### 7. Decide Whether Metadata Schema Needs Capability Fields

Status: no immediate schema extension indicated by coverage report.

Only extend `agentic-artifact/v2` if deterministic derivation still cannot
recover important cross-repo facts.

Candidate generic fields:

- `provides`
- `consumes`
- `validates`
- `interfaces`
- `capabilities`

Avoid adding `retrieval_profile` to authored headers unless it becomes a
deliberate schema decision. RAG-specific hints should stay generated by default.

Success criteria:

- schema extension is useful outside RAG
- checker and indexer validate it
- backfill can apply it in small governed batches
- generated recognition sources and RAG runtime stay fresh

### 8. Governed Header Backfill, If Needed

Status: not currently needed for retrieval-profile coverage.

If schema fields are added, use narrow governed batches. Do not hand-edit a
large repo-wide set.

Preferred command:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/backfill-v2-headers/script.sh --batch <1-15>
```

After each batch:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/check-headers/script.sh --all
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/generate-index/script.sh --all --pretty --strict >/tmp/artifact-index.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --write-all
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/evaluate-retrieval-selector-fixtures/smoke-test.sh
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/query-local-context/smoke-test.sh
```

### 9. Expand RAG Evaluations By Question Family

Status: in progress; first process-question repair complete in current branch,
pending commit.

Repeated misses should become fixtures, not ad hoc curated fixes.

Add fixtures for representative prompts across:

- artifact metadata and header maintenance
- harness indexing
- RAG index and selection behavior
- deploy corpus questions
- education corpus questions
- script ownership and command surfaces
- validation/check/gate questions

Success criteria:

- fixture failures point to a selector stage or missing profile signal
- RAG retrieves useful context without a custom term for every prompt
- source verification agrees with RAG for primary source families

2026-07-10 process-question A/B repair:

- sub-agent Cycle 3 found `0/10` strong verdicts for governed process
  questions because source search surfaced `.agentic` workflows, standards,
  state, commands, and script surfaces that RAG did not consistently preserve
  as primary evidence
- broad repair: index governed process sources automatically, add reusable
  question categories and evidence bundles, and add ten selector fixtures
  covering review agents, public beta portability, missing governance,
  governed scripts, education workflows, upstream reusable lessons, artifact
  path migration, chat command shortcuts, AWS workflow split, and rulebook
  coverage tracking
- post-repair A/B check: `10/10` realistic prompts returned strong verdicts
- selector regression: `62/62` fixtures passed
- commit gate: `scripts/02.rag-rulebook/commit-gates/script.sh` passed

2026-07-10 Cycle 4 source-family A/B repair:

- sub-agent Cycle 4 found `2/10` strong verdicts, with misses concentrated in
  source families that RAG could not yet preserve: deploy workflow/manifests,
  concrete container/runtime files, domain-corpus and OKF workflows, public
  article gates, article agent boundaries, packages/core source APIs, and the
  portable RAG service skeleton
- broad repair: index concrete source families for GitHub workflows, deploy
  infra, RAG rulebook service/process files, education ADRs, package source
  modules, and layer scripts; skip generic `workflows/default.md` files so
  trusted session metadata does not crowd out content evidence
- added reusable question categories, evidence bundles, and nine selector
  fixtures for the Cycle 4 source-family gaps
- post-repair A/B check: `10/10` realistic prompts returned strong verdicts
- selector regression: `71/71` fixtures passed

2026-07-10 Cycle 5 operational-diagnostics A/B repair:

- sub-agent Cycle 5 found `1/10` strong verdicts, with misses concentrated in
  operational diagnostics and validation wiring: hosted auth command behavior,
  runtime freshness, source projections, profile coverage, knowledge
  disposition, context-packet validation, recognition-source lifecycle, MCP
  deploy corpus gaps, and selector failure diagnosis
- broad repair: index RAG rulebook plans, policies, skills, recognition
  sources/candidates, corpus gaps, generated recognition sources, and
  diagnostic process artifacts as selectable process evidence
- added reusable question categories, evidence bundles, and ten selector
  fixtures for operational diagnostics and learner-facing index-selection
  prompts
- post-repair A/B check: `10/10` realistic prompts returned strong verdicts
- selector regression: `81/81` fixtures passed

## Resume Checklist

Use this checklist at the start of any future migration session:

```bash
git status --short --branch
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/check-headers/script.sh --all
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/01.harness/artifact-metadata/generate-index/script.sh --all --pretty --strict >/tmp/artifact-index.json
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --check
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/validate-recognition-sources/script.sh --current
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/build-local-runtime/script.sh --pretty
```

If any generated recognition source is stale, refresh it in the same slice:

```bash
bash scripts/01.harness/run-governed-script.sh --approved-action scripts/02.rag-rulebook/generate-recognition-sources/script.sh --write-all
```

## Drift Signals

Treat these as stop-and-investigate signals:

- v2-headered artifacts outside the strict index is greater than `0`
- strict index reports skipped files
- duplicate artifact IDs appear
- generated recognition source check fails after a clean regeneration
- selector smoke fails after adding or moving metadata-bearing artifacts
- RAG A/B source verification repeatedly finds primary source families missing
  from selected chunks

## Open Decisions

- Should profile coverage reporting live under `01.harness` because it starts
  from artifact metadata, or under `02.rag-rulebook` because it measures RAG
  utility?
- Which generic capability fields, if any, belong in `agentic-artifact/v2`?
- Should `backfill-v2-headers --status` expand to count `.github`, `infra`,
  and JS/MJS artifacts so its count aligns with the strict index?
- What threshold should make an artifact `weak` versus `partial`?
- Should generated profile confidence appear in context packets or stay in
  diagnostics only?
